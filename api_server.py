"""
FastAPI Server for Yuki AI Agent
Provides REST API endpoints for the Next.js frontend
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import asyncio
import json
import os
import sys
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Determine data paths (from environment or defaults)
DATA_PATH = os.getenv('WINDOWS_USE_DATA_PATH', os.path.join(os.getcwd(), 'data'))
LOGS_PATH = os.getenv('WINDOWS_USE_LOGS_PATH', os.path.join(os.getcwd(), 'logs'))
CONFIG_PATH = os.getenv('WINDOWS_USE_CONFIG_PATH', os.path.join(os.getcwd(), 'config'))
CACHE_PATH = os.getenv('WINDOWS_USE_CACHE_PATH', os.path.join(os.getcwd(), 'cache'))

# Create directories if they don't exist
for path in [DATA_PATH, LOGS_PATH, CONFIG_PATH, CACHE_PATH]:
    os.makedirs(path, exist_ok=True)

# Configure logging
log_file = os.path.join(LOGS_PATH, 'api_server.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
# First try config directory (for desktop app), then current directory
env_file_paths = [
    os.path.join(CONFIG_PATH, '.env'),
    os.path.join(os.getcwd(), '.env')
]

for env_path in env_file_paths:
    if os.path.exists(env_path):
        logger.info(f"Loading environment from: {env_path}")
        load_dotenv(env_path)
        break
else:
    logger.info("No .env file found, using system environment variables")
    load_dotenv()

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from windows_use.agent.service import Agent
from windows_use.agent.logger import agent_logger
from windows_use.agent.streaming_wrapper import StreamingAgentWrapper
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from main import get_running_programs
import threading
import uuid
import re

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    # Log session start (matching CLI behavior)
    agent_logger.log_session_start()
    logger.info("Session logging started")
    
    # Try to create default API keys file if it doesn't exist
    config_file = os.path.join(CONFIG_PATH, "api_keys.json")
    if not os.path.exists(config_file):
        logger.info("Creating default API keys file...")
        print("🔧 Creating default API keys file...")
        try:
            default_config = {
                "google_api_key": "",
                "elevenlabs_api_key": "",
                "deepgram_api_key": "",
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # Ensure config directory exists
            os.makedirs(CONFIG_PATH, exist_ok=True)
            
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Default API keys file created at: {config_file}")
            print(f"✅ Default API keys file created at: {config_file}")
            print("📝 Please configure your API keys in the settings page")
            
        except Exception as e:
            logger.error(f"Failed to create default API keys file: {e}")
            print(f"❌ Failed to create default API keys file: {e}")
            
    # Initialize agent (will fail gracefully if no API key)
    await initialize_agent()
    # Load persisted scheduled tasks and re-schedule future ones
    try:
        _load_scheduled_tasks()
        with _scheduled_lock:
            for task in list(_scheduled_tasks.values()):
                # Only reschedule tasks that are still pending
                if task.status in ("scheduled", "running"):
                    # recompute scheduled_for
                    if task.delay_seconds is not None:
                        task.scheduled_for = None
                    elif task.run_at:
                        # keep as provided
                        task.scheduled_for = task.run_at
                    _scheduled_tasks[task.id] = task
                    _schedule_timer_for_task(task)
    except Exception as e:
        logger.warning(f"Scheduled tasks reload failed: {e}")
    
    yield  # Application is running
    
    # Shutdown
    try:
        logger.info("Server shutdown initiated")
        # Log session end (matching CLI behavior)
        agent_logger.log_session_end()
        logger.info("Session logged successfully on shutdown")
        print("Session logged successfully on shutdown.")
    except Exception as e:
        logger.error(f"Error logging session end: {e}")
        print(f"Error logging session end: {e}")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Yuki AI Agent API",
    description="REST API for Yuki AI automation agent",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent: Optional[Agent] = None
streaming_wrapper: Optional[StreamingAgentWrapper] = None
agent_initialized = False

# Function to initialize the agent (can be called multiple times)
async def initialize_agent():
    """Initialize or re-initialize the agent with current API keys"""
    global agent, streaming_wrapper, agent_initialized
    
    try:
        logger.info("Starting agent initialization...")
        print("Initializing Yuki AI Agent...")
        
        # Get Google API key from config file
        config_file = os.path.join(CONFIG_PATH, "api_keys.json")
        google_api_key = ""
        
        logger.info(f"Looking for API keys in config file: {config_file}")
        print(f"🔍 Looking for API keys in: {config_file}")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    google_api_key = config_data.get("google_api_key", "")
                    logger.info(f"Found Google API key: {'Yes' if google_api_key else 'No'}")
                    print(f"✅ Config file found - Google API key: {'Yes' if google_api_key else 'No'}")
            except Exception as e:
                logger.error(f"Error reading config file: {e}")
                print(f"❌ Error reading config file: {e}")
        else:
            logger.warning(f"Config file not found: {config_file}")
            print(f"⚠️  Config file not found: {config_file}")
        
        if not google_api_key or not google_api_key.strip():
            error_msg = "Google API key is not set. Please configure it in the settings page."
            logger.error(error_msg)
            print(f"🚨 {error_msg}")
            agent_initialized = False
            return False
        
        logger.info("Initializing ChatGoogleGenerativeAI...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            temperature=0.3,
            google_api_key=google_api_key
        )
        logger.info("ChatGoogleGenerativeAI initialized successfully")
        
        # TTS configuration - check if ElevenLabs API key is available
        enable_tts = False
        tts_voice_id = "21m00Tcm4TlvDq8ikWAM"
        
        logger.info("Checking TTS configuration...")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    elevenlabs_key = config_data.get("elevenlabs_api_key", "")
                    if elevenlabs_key and elevenlabs_key.strip():
                        enable_tts = True
                        logger.info("ElevenLabs API key found, TTS enabled")
                    else:
                        logger.info("No ElevenLabs API key found, TTS disabled")
            except Exception as e:
                logger.error(f"Error reading ElevenLabs API key: {e}")
        
        # Initialize agent
        logger.info("Initializing Agent with parameters...")
        agent = Agent(
            llm=llm,
            browser='chrome',
            use_vision=False,
            enable_conversation=True,
            literal_mode=True,
            max_steps=100,
            enable_tts=enable_tts,
            tts_voice_id=tts_voice_id
        )
        logger.info("Agent initialized successfully")
        
        # Get running programs
        logger.info("Getting running programs...")
        running_programs = get_running_programs()
        agent.running_programs = running_programs
        logger.info(f"Found {len(running_programs)} running programs")
        
        # Pre-warm the system
        logger.info("Pre-warming system for faster response...")
        print("Pre-warming system for faster response...")
        try:
            agent.desktop.get_state(use_vision=False)
            logger.info("System pre-warmed successfully")
            print("System pre-warmed successfully!")
        except Exception as e:
            logger.warning(f"Pre-warming failed: {e}")
            print(f"Pre-warming failed: {e}")
        
        # Show TTS status
        if enable_tts:
            from windows_use.agent.tts_service import is_tts_available
            tts_available = is_tts_available()
            tts_status = 'Enabled' if tts_available else 'Disabled (API key not configured)'
            logger.info(f"TTS Status: {tts_status}")
            print(f"TTS Status: {tts_status}")
        else:
            logger.info("TTS Status: Disabled")
            print("TTS Status: Disabled")
        
        # Create streaming wrapper
        logger.info("Creating streaming wrapper...")
        streaming_wrapper = StreamingAgentWrapper(agent)
        logger.info("Streaming wrapper created")
        
        agent_initialized = True
        logger.info("Agent initialization completed successfully")
        print("Agent initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        print(f"Failed to initialize agent: {e}")
        agent_initialized = False
        return False

# In-flight request tracking for cooperative stop
inflight_requests: Dict[str, Dict[str, Any]] = {}

# Request/Response Models
class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class QueryRequest(BaseModel):
    query: str
    use_vision: bool = False
    conversation_history: List[ConversationMessage] = []
    api_key: str  # Frontend must provide API key
    request_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    success: bool
    timestamp: datetime
    error: Optional[str] = None

class AppInfo(BaseModel):
    name: str
    title: str
    id: str

class SystemStatus(BaseModel):
    agent_ready: bool
    running_programs: List[AppInfo]
    memory_stats: Dict[str, Any]
    performance_stats: Dict[str, Any]

class SettingsRequest(BaseModel):
    enable_tts: bool = True
    tts_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    cache_timeout: float = 2.0
    max_steps: int = 50

class ApiKeysRequest(BaseModel):
    google_api_key: str
    elevenlabs_api_key: str = ""
    deepgram_api_key: str = ""

class ApiKeysResponse(BaseModel):
    google_api_key: str
    elevenlabs_api_key: str
    deepgram_api_key: str

# Scheduled tasks
class ScheduledTask(BaseModel):
    id: str
    name: str | None = None
    query: str | None = None
    delay_seconds: Optional[int] = None
    run_at: Optional[str] = None  # ISO string or HH:MM
    status: str = "scheduled"  # scheduled, running, completed, cancelled, failed
    created_at: str
    scheduled_for: Optional[str] = None
    last_error: Optional[str] = None

# In-memory registry and persistence for scheduled tasks
_scheduled_tasks: Dict[str, ScheduledTask] = {}
_scheduled_timers: Dict[str, threading.Timer] = {}
_scheduled_lock = threading.Lock()
SCHEDULED_TASKS_FILE = os.path.join(DATA_PATH, "scheduled_tasks.json")

def _parse_run_at_to_delay(run_at_text: str) -> Optional[float]:
    text = (run_at_text or "").strip()
    if not text:
        return None

def _extract_time_from_text(text: str) -> tuple[Optional[int], Optional[str]]:
    """Extract delay_seconds or run_at from natural language like 'in 20 minutes', 'in around 50 seconds', 'at 10:30 am'.
    Returns (delay_seconds, run_at_iso_or_HHMM) with only one populated.
    """
    if not text:
        return (None, None)
    lowered = text.lower().strip()
    # in X seconds/minutes/hours
    m = re.search(r"in\s+(?:about|around\s+)?(\d+)\s*(seconds?|mins?|minutes?|hours?|hrs?)", lowered)
    if m:
        amount = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("sec"):
            return (amount, None)
        if unit.startswith("min"):
            return (amount * 60, None)
        if unit.startswith("hour") or unit.startswith("hr"):
            return (amount * 3600, None)
    # at HH:MM [am|pm]
    m2 = re.search(r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", lowered)
    if m2:
        hh = int(m2.group(1))
        mm = int(m2.group(2) or 0)
        ap = (m2.group(3) or '').lower()
        if ap in ("am", "pm"):
            if hh == 12:
                hh = 0
            if ap == "pm":
                hh += 12
        # Return HH:MM in 24h
        return (None, f"{hh:02d}:{mm:02d}")
    return (None, None)
    now = datetime.now()
    try:
        if len(text) in (4,5) and ":" in text:
            hh, mm = text.split(":", 1)
            target = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
        else:
            target = datetime.fromisoformat(text)
            if target <= now:
                return None
        return max(0.0, (target - now).total_seconds())
    except Exception:
        return None

def _persist_scheduled_tasks() -> None:
    try:
        with open(SCHEDULED_TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump({tid: t.model_dump() for tid, t in _scheduled_tasks.items()}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Failed to persist scheduled tasks: {e}")

def _load_scheduled_tasks() -> None:
    if not os.path.exists(SCHEDULED_TASKS_FILE):
        return
    try:
        with open(SCHEDULED_TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for tid, tdict in data.items():
                try:
                    _scheduled_tasks[tid] = ScheduledTask(**tdict)
                except Exception:
                    continue
    except Exception as e:
        logger.warning(f"Failed to load scheduled tasks: {e}")

def _schedule_timer_for_task(task: ScheduledTask) -> None:
    if not agent_initialized or not agent:
        return
    # compute delay
    delay: Optional[float] = None
    if task.delay_seconds is not None:
        delay = max(0.0, float(task.delay_seconds))
    elif task.run_at:
        delay = _parse_run_at_to_delay(task.run_at)
    if delay is None:
        with _scheduled_lock:
            t = _scheduled_tasks.get(task.id)
            if t:
                t.status = "failed"
                t.last_error = "Invalid schedule time"
                _scheduled_tasks[task.id] = t
                _persist_scheduled_tasks()
        return

    def _run():
        try:
            with _scheduled_lock:
                t = _scheduled_tasks.get(task.id)
                if not t or t.status in ("cancelled",):
                    return
                t.status = "running"
                _scheduled_tasks[task.id] = t
                _persist_scheduled_tasks()
            # Launch app
            status = 0
            response = ""
            if task.query and task.query.strip():
                try:
                    # Run full agent query
                    agent.invoke(task.query)
                    status = 0
                except Exception as e:
                    status = 1
                    response = str(e)
            elif task.name:
                app_name, response, status = agent.desktop.launch_app(task.name)
                try:
                    # Best-effort: ensure it comes to foreground once to avoid stale state
                    if status == 0 and app_name:
                        agent.desktop.switch_app(app_name)
                except Exception:
                    pass
            else:
                status = 1
                response = "Task missing name or query"
            with _scheduled_lock:
                t = _scheduled_tasks.get(task.id)
                if t:
                    t.status = "completed" if status == 0 else "failed"
                    if status != 0:
                        t.last_error = response
                    _scheduled_tasks[task.id] = t
                    _persist_scheduled_tasks()
        except Exception as e:
            with _scheduled_lock:
                t = _scheduled_tasks.get(task.id)
                if t:
                    t.status = "failed"
                    t.last_error = str(e)
                    _scheduled_tasks[task.id] = t
                    _persist_scheduled_tasks()

    timer = threading.Timer(delay, _run)
    timer.daemon = True
    with _scheduled_lock:
        # cancel existing
        old = _scheduled_timers.pop(task.id, None)
        if old:
            try:
                old.cancel()
            except Exception:
                pass
        _scheduled_timers[task.id] = timer
    timer.start()

class VoiceModeRequest(BaseModel):
    # Frontend may omit this; backend uses server-side env keys for voice mode
    api_key: Optional[str] = None


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info(f"Health check requested - agent_ready: {agent_initialized}")
    return {
        "status": "healthy",
        "agent_ready": agent_initialized,
        "timestamp": datetime.now().isoformat()
    }

# Simple connectivity test endpoint
@app.get("/api/test")
async def test_connection():
    """Simple test endpoint for frontend connectivity"""
    return {
        "message": "API server is reachable",
        "timestamp": datetime.now().isoformat(),
        "server_host": "127.0.0.1:8000"
    }

# System status endpoint
@app.get("/api/status", response_model=SystemStatus)
async def get_system_status():
    """Get current system status"""
    logger.info(f"System status requested - agent_initialized: {agent_initialized}, agent: {agent is not None}")
    if not agent_initialized or not agent:
        logger.error("System status requested but agent not initialized")
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        logger.info("Getting running programs...")
        # Get running programs
        running_programs = get_running_programs()
        apps = [
            AppInfo(name=prog['name'], title=prog['title'], id=str(prog['id']))
            for prog in running_programs
        ]
        logger.info(f"Found {len(apps)} running programs")
        
        # Get memory stats
        memory_stats = {}
        try:
            if hasattr(agent, 'get_memory_stats'):
                memory_stats = agent.get_memory_stats()
                logger.info("Memory stats retrieved successfully")
        except Exception as e:
            logger.warning(f"Failed to get memory stats: {e}")
        
        # Get performance stats
        performance_stats = {}
        try:
            if hasattr(agent, 'performance_monitor'):
                performance_stats = agent.performance_monitor.get_stats()
                logger.info("Performance stats retrieved successfully")
        except Exception as e:
            logger.warning(f"Failed to get performance stats: {e}")
        
        logger.info("System status retrieved successfully")
        return SystemStatus(
            agent_ready=True,
            running_programs=apps,
            memory_stats=memory_stats,
            performance_stats=performance_stats
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")

# Query endpoint
@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """Process a query through the agent"""
    logger.info(f"Query request received: {request.query[:100]}...")
    if not agent_initialized or not agent:
        logger.error("Query requested but agent not initialized")
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Process the query (matching CLI behavior)
        logger.info(f"Processing query: {request.query}")
        print(f"Processing query: {request.query}")
        response = agent.invoke(request.query)
        
        # Extract response content (matching CLI behavior)
        if hasattr(response, 'content') and response.content:
            response_text = response.content
        else:
            response_text = str(response)
        
        logger.info(f"Query processed successfully, response length: {len(response_text)}")
        print(f"Response: {response_text[:100]}...")  # Log first 100 chars
        
        return QueryResponse(
            response=response_text,
            success=True,
            timestamp=datetime.now(),
            error=None
        )
        
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        print(f"Query processing error: {e}")
        return QueryResponse(
            response="",
            success=False,
            timestamp=datetime.now(),
            error=("Execution stopped by user" if str(e).strip().lower() == "execution stopped by user" else str(e))
        )

# Streaming query endpoint for real-time responses
@app.post("/api/query/stream")
async def process_query_stream(request: QueryRequest):
    """Process a query with streaming response - shows full agent workflow"""
    if not agent_initialized or not streaming_wrapper:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    async def generate_response():
        try:
            print(f"Streaming query: {request.query}")
            
            # Get API key from config file or frontend
            config_file = os.path.join(CONFIG_PATH, "api_keys.json")
            google_api_key = ""
            
            if os.path.exists(config_file):
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        google_api_key = config_data.get("google_api_key", "")
                except:
                    pass
            
            # Use frontend API key if provided, otherwise use config file
            if request.api_key and request.api_key.strip():
                google_api_key = request.api_key.strip()
                print("Using API key from frontend")
            elif google_api_key:
                print("Using API key from config file")
            else:
                yield f"data: {json.dumps({'type': 'error', 'timestamp': datetime.now().isoformat(), 'data': {'message': 'API key is required. Please set it in settings.'}})}\n\n"
                return
            
            # Create new agent instance with API key
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash", 
                temperature=0.3,
                google_api_key=google_api_key
            )
            
            # Create a new agent instance with the frontend API key
            frontend_agent = Agent(
                llm=llm,
                browser='chrome',
                use_vision=False,
                enable_conversation=True,
                literal_mode=True,
                max_steps=50,
                enable_tts=False,  # We'll handle TTS separately
                tts_voice_id="21m00Tcm4TlvDq8ikWAM"
            )
            
            # Copy running programs from the original agent
            frontend_agent.running_programs = agent.running_programs
            
            # Create a dedicated streaming wrapper for this frontend agent
            frontend_streaming_wrapper = StreamingAgentWrapper(frontend_agent)
            
            # Load conversation history into agent if provided
            if request.conversation_history:
                conversation_messages = []
                for msg in request.conversation_history:
                    if msg.role == "user":
                        conversation_messages.append(HumanMessage(content=msg.content))
                    elif msg.role == "assistant":
                        conversation_messages.append(AIMessage(content=msg.content))
                
                # Set conversation history on the agent
                if hasattr(frontend_agent, 'conversation_history'):
                    frontend_agent.conversation_history = conversation_messages
                    print(f"Loaded {len(conversation_messages)} messages from conversation history")
            
            # Container for the result
            result_container = {"response": None, "error": None, "done": False}

            # Assign or generate request_id and register inflight request
            req_id = request.request_id or str(uuid.uuid4())
            
            # Store session conversation for future reference
            if req_id:
                session_conversations[req_id] = request.conversation_history
            inflight_requests[req_id] = {
                "agent": frontend_agent,
                "thread": None,
                "created_at": time.time(),
            }

            # Emit start event with request_id
            start_update = {
                "type": "start",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "request_id": req_id,
                    "message": "Started processing",
                },
            }
            yield f"data: {json.dumps(start_update)}\n\n"
            
            def run_agent():
                """Run agent in background thread"""
                try:
                    result_container["response"] = frontend_agent.invoke(request.query)
                    result_container["done"] = True
                except Exception as e:
                    result_container["error"] = e
                    result_container["done"] = True
            
            # Start agent in background thread
            thread = threading.Thread(target=run_agent)
            inflight_requests[req_id]["thread"] = thread
            thread.start()
            
            # Stream status updates while agent is running
            last_status = None
            while not result_container["done"]:
                # Get new status updates from the frontend agent's streaming wrapper
                updates = frontend_streaming_wrapper.get_status_updates()
                
                for update in updates:
                    status = update["status"]
                    action_name = update["action_name"]
                    details = update["details"]
                    
                    # Determine update type based on status
                    if status == "Thinking":
                        update_type = "thinking"
                        message = f"{action_name}" + (f": {details}" if details else "")
                    elif status == "Reasoning":
                        update_type = "reasoning"
                        message = details if details else "Agent is thinking..."
                    elif status == "Executing":
                        update_type = "tool_use"
                        message = f"Using {action_name}"
                        tool_name = action_name
                    elif status in ["Completed", "Failed"]:
                        update_type = "tool_result"
                        message = f"{status}: {action_name}"
                    elif status == "Refreshing":
                        update_type = "status"
                        message = f"{action_name}: {details}" if details else action_name
                    elif status == "Finalizing":
                        update_type = "thinking"
                        message = "Preparing final response..."
                    else:
                        update_type = "status"
                        message = f"{status}" + (f": {action_name}" if action_name else "")
                    
                    # Send the update
                    stream_update = {
                        "type": update_type,
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "message": message,
                            "status": status,
                            "action_name": action_name,
                            "details": details
                        }
                    }
                    
                    # Add tool-specific data
                    if update_type == "tool_use" and action_name:
                        stream_update["data"]["tool_name"] = action_name
                    
                    yield f"data: {json.dumps(stream_update)}\n\n"
                    last_status = update
                
                # Small delay to avoid busy-waiting
                await asyncio.sleep(0.1)
            
            # Wait for thread to finish
            thread.join(timeout=1.0)
            
            # Check for errors
            if result_container["error"]:
                raise result_container["error"]
            
            # Extract and send final response or error
            response = result_container["response"]
            # If AgentResult-like with error, emit error event
            if hasattr(response, 'error') and response.error:
                err_msg = str(response.error) if response.error is not None else ""
                # Normalize user-stop message
                cleaned = err_msg.strip()
                if cleaned.lower().endswith("execution stopped by user"):
                    cleaned = "Execution stopped by user"
                error_update = {
                    "type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "message": cleaned,
                        "error_type": "Stopped" if cleaned == "Execution stopped by user" else "AgentError"
                    }
                }
                yield f"data: {json.dumps(error_update)}\n\n"
            else:
                if hasattr(response, 'content') and response.content:
                    response_text = response.content
                else:
                    response_text = str(response)
                response_update = {
                    "type": "response",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "message": response_text,
                        "success": True
                    }
                }
                yield f"data: {json.dumps(response_update)}\n\n"
            
            # Send completion
            complete_update = {
                "type": "complete",
                "timestamp": datetime.now().isoformat(),
                "data": {"message": "Done"}
            }
            yield f"data: {json.dumps(complete_update)}\n\n"

            # Cleanup inflight request
            inflight_requests.pop(req_id, None)
            
        except Exception as e:
            import traceback
            print(f"Streaming error: {e}\n{traceback.format_exc()}")
            error_update = {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "message": ("Execution stopped by user" if str(e).strip().lower() == "execution stopped by user" else str(e)),
                    "error_type": type(e).__name__
                }
            }
            yield f"data: {json.dumps(error_update)}\n\n"
        finally:
            # Best-effort cleanup if exception path
            if 'req_id' in locals():
                inflight_requests.pop(req_id, None)
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Stop an in-flight text request
class StopRequest(BaseModel):
    request_id: str

@app.post("/api/query/stop")
async def stop_query(request: StopRequest):
    """Cooperatively stop a running query by request_id."""
    if not agent_initialized:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    info = inflight_requests.get(request.request_id)
    if not info:
        return {"success": False, "message": "Request not found or already finished"}
    try:
        agent_to_stop = info.get("agent")
        if hasattr(agent_to_stop, "stop"):
            agent_to_stop.stop()
        return {"success": True, "message": "Stop requested"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop: {e}")

@app.post("/api/query/stop-all")
async def stop_all_queries():
    """Stop all currently running queries."""
    if not agent_initialized:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    stopped_count = 0
    errors = []
    
    # Make a copy of the dict to avoid modification during iteration
    requests_to_stop = dict(inflight_requests)
    
    for req_id, info in requests_to_stop.items():
        try:
            agent_to_stop = info.get("agent")
            if agent_to_stop and hasattr(agent_to_stop, "stop"):
                agent_to_stop.stop()
                stopped_count += 1
        except Exception as e:
            errors.append(f"Failed to stop request {req_id}: {e}")
    
    # Clean up stopped requests
    for req_id in requests_to_stop.keys():
        inflight_requests.pop(req_id, None)
    
    return {
        "success": True,
        "message": f"Stopped {stopped_count} request(s)",
        "stopped_count": stopped_count,
        "errors": errors if errors else None
    }

# Get running programs
@app.get("/api/programs", response_model=List[AppInfo])
async def get_running_programs_endpoint():
    """Get list of currently running programs"""
    try:
        programs = get_running_programs()
        return [
            AppInfo(name=prog['name'], title=prog['title'], id=str(prog['id']))
            for prog in programs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting programs: {str(e)}")

# Clear conversation
@app.post("/api/conversation/clear")
async def clear_conversation():
    """Clear the conversation history"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        agent.clear_conversation()
        return {"success": True, "message": "Conversation cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")

# Get memories
@app.get("/api/memories")
async def get_memories():
    """Get stored memories"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if hasattr(agent, 'list_memories'):
            memories = agent.list_memories()
            return {"memories": memories}
        else:
            return {"memories": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting memories: {str(e)}")

# Clear memories
@app.post("/api/memories/clear")
async def clear_memories():
    """Clear all stored memories"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if hasattr(agent, 'clear_memories'):
            agent.clear_memories()
            return {"success": True, "message": "Memories cleared"}
        else:
            return {"success": False, "message": "Memory system not available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing memories: {str(e)}")

# Update settings
@app.post("/api/settings")
async def update_settings(request: SettingsRequest):
    """Update agent settings"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Update TTS settings
        if hasattr(agent, 'tts_service') and agent.tts_service:
            agent.tts_service.enabled = request.enable_tts
            agent.tts_service.voice_id = request.tts_voice_id
        
        # Update cache timeout
        if hasattr(agent, 'desktop'):
            agent.desktop.cache_timeout = request.cache_timeout
        
        # Update max steps
        agent.max_steps = request.max_steps
        
        return {"success": True, "message": "Settings updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")

# Get performance stats
@app.get("/api/performance")
async def get_performance_stats():
    """Get performance statistics"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        stats = {}
        
        # Agent performance stats
        if hasattr(agent, 'performance_monitor'):
            stats['agent'] = agent.performance_monitor.get_stats()
        
        # Detection system stats
        if hasattr(agent, 'desktop') and hasattr(agent.desktop, 'get_detection_stats'):
            stats['detection'] = agent.desktop.get_detection_stats()
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance stats: {str(e)}")

# TTS control endpoints
@app.post("/api/tts/start")
async def start_speaking(text: str):
    """Start text-to-speech"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if hasattr(agent, 'tts_service') and agent.tts_service and agent.tts_service.enabled:
            agent.tts_service.speak_async(text)
            return {"success": True, "message": "Started speaking"}
        else:
            return {"success": False, "message": "TTS not available or disabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting TTS: {str(e)}")

@app.post("/api/tts/stop")
async def stop_speaking():
    """Stop text-to-speech"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if hasattr(agent, 'stop_speaking'):
            agent.stop_speaking()
            return {"success": True, "message": "Stopped speaking"}
        else:
            return {"success": False, "message": "Stop speaking not available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping TTS: {str(e)}")

# Voice conversation storage
voice_conversation = []
# Track the index of the current assistant placeholder message during voice processing
voice_current_assistant_index: Optional[int] = None
# Last processed voice command to avoid duplicates when STT emits repeated finals
voice_last_command_text: Optional[str] = None
voice_last_command_ts: float = 0.0

# Session-based conversation storage
session_conversations: Dict[str, List[Dict[str, Any]]] = {}
# Default session id for single-chat UI
DEFAULT_SESSION_ID = "default"

# Global flags to prevent duplicate voice processing/starts
_voice_processing_lock = False
_voice_starting = False

@app.get("/api/voice/conversation")
async def get_voice_conversation():
    """Get the latest voice conversation"""
    return {"conversation": voice_conversation}

# Session-based conversation endpoints
@app.get("/api/conversation/{session_id}")
async def get_session_conversation(session_id: str):
    """Get conversation for a specific session"""
    if session_id not in session_conversations:
        return {"conversation": []}
    return {"conversation": session_conversations[session_id]}

@app.post("/api/conversation/{session_id}")
async def save_session_conversation(session_id: str, conversation: List[Dict[str, Any]]):
    """Save conversation for a specific session"""
    session_conversations[session_id] = conversation
    return {"success": True, "message": "Conversation saved"}

@app.delete("/api/conversation/{session_id}")
async def clear_session_conversation(session_id: str):
    """Clear conversation for a specific session"""
    if session_id in session_conversations:
        del session_conversations[session_id]
    return {"success": True, "message": "Conversation cleared"}

# Default-session conversation endpoints (no session_id in path)
@app.get("/api/conversation")
async def get_default_conversation():
    """Get conversation for the default session (no path param)."""
    return {"conversation": session_conversations.get(DEFAULT_SESSION_ID, [])}

@app.post("/api/conversation")
async def save_default_conversation(conversation: List[Dict[str, Any]]):
    """Save conversation for the default session (no path param)."""
    session_conversations[DEFAULT_SESSION_ID] = conversation
    return {"success": True, "message": "Conversation saved"}

@app.delete("/api/conversation")
async def clear_default_conversation():
    """Clear conversation for the default session (no path param)."""
    if DEFAULT_SESSION_ID in session_conversations:
        del session_conversations[DEFAULT_SESSION_ID]
    return {"success": True, "message": "Conversation cleared"}

# Voice mode control endpoints
@app.post("/api/voice/start")
async def start_voice_mode(request: VoiceModeRequest):
    """Start voice mode using backend STT/TTS"""
    print("[Voice Mode Backend] /api/voice/start endpoint called")
    print(f"[Voice Mode Backend] Request body: {request}")
    print(f"[Voice Mode Backend] Agent initialized: {agent_initialized}, Agent exists: {agent is not None}")
    
    if not agent_initialized or not agent:
        print("[Voice Mode Backend] ERROR: Agent not initialized")
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        global _voice_starting
        print(f"[Voice Mode Backend] Current _voice_starting flag: {_voice_starting}")
        # If a start is already in progress, return early
        if _voice_starting:
            print("[Voice Mode Backend] Voice mode already starting, returning early")
            return {"success": True, "message": "Voice mode starting"}
        _voice_starting = True
        print("[Voice Mode Backend] Set _voice_starting to True")
        # Check if STT dependencies are available (without creating global instance)
        print("[Voice Mode Backend] Checking STT dependencies...")
        try:
            from windows_use.agent.stt_service import DEEPGRAM_AVAILABLE
            print(f"[Voice Mode Backend] DEEPGRAM_AVAILABLE: {DEEPGRAM_AVAILABLE}")
            if not DEEPGRAM_AVAILABLE:
                print("[Voice Mode Backend] ERROR: Deepgram SDK not available")
                raise HTTPException(status_code=400, detail="Deepgram SDK not available. Install with: pip install deepgram-sdk")
            
            # Check for API key from config file
            config_file = os.path.join(CONFIG_PATH, "api_keys.json")
            print(f"[Voice Mode Backend] Checking config file: {config_file}")
            deepgram_key = ""
            
            if os.path.exists(config_file):
                print("[Voice Mode Backend] Config file exists, reading...")
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        deepgram_key = config_data.get("deepgram_api_key", "")
                        print(f"[Voice Mode Backend] Deepgram API key found: {'present' if deepgram_key else 'missing'}")
                except Exception as e:
                    print(f"[Voice Mode Backend] Error reading config file: {e}")
                    pass
            else:
                print("[Voice Mode Backend] Config file does not exist")
            
            if not deepgram_key or deepgram_key.strip() == "":
                print("[Voice Mode Backend] ERROR: Deepgram API key not configured")
                raise HTTPException(status_code=400, detail="Deepgram API key not configured. Please set it in the settings page.")
        except ImportError as e:
            print(f"[Voice Mode Backend] ERROR: STT service import error: {e}")
            raise HTTPException(status_code=400, detail=f"STT service import error: {str(e)}")
        
        # Reuse existing STT service if already present
        print("[Voice Mode Backend] Initializing STT service...")
        from windows_use.agent.stt_service import STTService
        voice_stt_service = None
        if hasattr(agent, 'stt_service') and agent.stt_service:
            print("[Voice Mode Backend] Reusing existing STT service")
            voice_stt_service = agent.stt_service
        else:
            print("[Voice Mode Backend] Creating new STT service with trigger word 'yuki'")
            voice_stt_service = STTService(enable_stt=True, trigger_word="yuki")
            print(f"[Voice Mode Backend] STT service enabled: {voice_stt_service.enabled}")
            if not voice_stt_service.enabled:
                print("[Voice Mode Backend] ERROR: STT service could not be initialized")
                _voice_starting = False
                raise HTTPException(status_code=400, detail="STT service could not be initialized. Check your Deepgram API key.")
            agent.stt_service = voice_stt_service
            print("[Voice Mode Backend] STT service assigned to agent")
        
        # Enable TTS for voice mode if not already enabled
        print("[Voice Mode Backend] Checking TTS service...")
        if not hasattr(agent, 'tts_service') or not agent.tts_service or not agent.tts_service.enabled:
            print("[Voice Mode Backend] TTS not enabled, initializing...")
            from windows_use.agent.tts_service import TTSService
            tts_service = TTSService(enable_tts=True)
            print(f"[Voice Mode Backend] TTS service enabled: {tts_service.enabled}")
            if tts_service.enabled:
                agent.tts_service = tts_service
                print("[Voice Mode Backend] TTS service assigned to agent")
        else:
            print("[Voice Mode Backend] TTS service already enabled")
        
        # Set up transcription callback to handle voice input with trigger word detection
        def on_transcription(transcript: str):
            """Handle voice transcription and send to chat (only triggered commands after 'yuki')"""
            global _voice_processing_lock
            global voice_current_assistant_index
            global voice_last_command_text, voice_last_command_ts
            
            # BULLETPROOF DUPLICATE PREVENTION
            if _voice_processing_lock:
                print(f"DUPLICATE PREVENTED: {transcript}")
                return
            
            _voice_processing_lock = True
            
            # Check if we're waiting for a command after trigger word detection
            if voice_stt_service.is_waiting_for_command():
                print(f"Voice command received: {transcript}")
            else:
                print(f"Trigger word detected, voice command received: {transcript}")
            
            try:
                # Normalize transcript: strip trigger word 'yuki' prefix if present
                norm = transcript.strip()
                low = norm.lower()
                if low.startswith("yuki"):
                    norm = norm[len("yuki"):].lstrip(" ,:.-")
                elif low.startswith("hey yuki"):
                    norm = norm[len("hey yuki"):].lstrip(" ,:.-")
                elif low.startswith("hi yuki"):
                    norm = norm[len("hi yuki"):].lstrip(" ,:.-")
                if not norm:
                    # Nothing meaningful after trigger
                    _voice_processing_lock = False
                    return

                # Deduplicate same command within a short window (e.g., 4 seconds)
                now_ts = time.time()
                if voice_last_command_text is not None:
                    same_text = norm.strip().lower() == voice_last_command_text.strip().lower()
                    if same_text and (now_ts - voice_last_command_ts) < 4.0:
                        print(f"VOICE DEDUP: ignoring duplicate command within window: {norm}")
                        _voice_processing_lock = False
                        return

                # Store user message
                voice_conversation.append({
                    "role": "user",
                    "content": norm,
                    "timestamp": time.time()
                })
                
                # Create a placeholder assistant message to accumulate live workflow steps
                placeholder = {
                    "role": "assistant",
                    "content": "",  # will be filled when final response is ready
                    "timestamp": time.time(),
                    "workflowSteps": []
                }
                voice_conversation.append(placeholder)
                voice_current_assistant_index = len(voice_conversation) - 1
                
                # Process the transcript through the agent with workflow step capture
                # Create a new agent instance for voice processing (isolated from global agent)
                from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
                # Get Google API key from config file
                config_file = os.path.join(CONFIG_PATH, "api_keys.json")
                google_api_key = ""
                
                if os.path.exists(config_file):
                    try:
                        with open(config_file, "r", encoding="utf-8") as f:
                            config_data = json.load(f)
                            google_api_key = config_data.get("google_api_key", "")
                    except:
                        pass
                
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash", 
                    temperature=0.3,
                    google_api_key=google_api_key
                )
                
                voice_agent = Agent(
                    llm=llm,
                    browser='chrome',
                    use_vision=False,
                    enable_conversation=True,
                    literal_mode=True,
                    max_steps=50,
                    enable_tts=False  # We'll handle TTS separately
                )
                
                # Copy running programs from the main agent
                voice_agent.running_programs = agent.running_programs
                
                # Capture workflow steps by temporarily overriding show_status method
                workflow_steps = []
                original_show_status = voice_agent.show_status
                
                def capture_show_status(status: str, action_name: str = None, details: str = None):
                    """Capture workflow steps while maintaining console output"""
                    # Call original method for console output
                    original_show_status(status, action_name, details)
                    
                    # Determine update type based on status (same logic as text mode)
                    if status == "Thinking":
                        update_type = "thinking"
                        message = f"{action_name}" + (f": {details}" if details else "")
                    elif status == "Reasoning":
                        update_type = "reasoning"
                        message = details if details else "Agent is thinking..."
                    elif status == "Executing":
                        update_type = "tool_use"
                        message = f"Using {action_name}"
                    elif status in ["Completed", "Failed"]:
                        update_type = "tool_result"
                        message = f"{status}: {action_name}"
                    elif status == "Refreshing":
                        update_type = "status"
                        message = f"{action_name}: {details}" if details else action_name
                    elif status == "Finalizing":
                        update_type = "thinking"
                        message = "Preparing final response..."
                    elif status == "Starting":
                        update_type = "thinking"
                        message = f"{action_name}: {details}" if details else action_name
                    else:
                        update_type = "status"
                        message = f"{status}" + (f": {action_name}" if action_name else "")
                    
                    # Capture workflow step
                    workflow_steps.append({
                        "type": update_type,
                        "message": message,
                        "timestamp": time.time(),
                        "status": status,
                        "actionName": action_name
                    })

                    # Also update the live placeholder assistant message so UI can poll and render steps
                    try:
                        if voice_current_assistant_index is not None and 0 <= voice_current_assistant_index < len(voice_conversation):
                            current_msg = voice_conversation[voice_current_assistant_index]
                            steps = current_msg.get("workflowSteps", [])
                            steps.append({
                                "type": update_type,
                                "message": message,
                                "timestamp": time.time(),
                                "status": status,
                                "actionName": action_name
                            })
                            current_msg["workflowSteps"] = steps
                            current_msg["timestamp"] = time.time()
                    except Exception as _:
                        pass
                
                # Apply the override
                voice_agent.show_status = capture_show_status
                
                try:
                    # Process the voice query normally
                    response = voice_agent.invoke(norm)
                finally:
                    # Always restore the original method
                    voice_agent.show_status = original_show_status

                # Mark this command as processed
                voice_last_command_text = norm
                voice_last_command_ts = now_ts
                
                if response and hasattr(response, 'content') and response.content:
                    # Finalize the placeholder assistant message with content and captured steps
                    if voice_current_assistant_index is not None and 0 <= voice_current_assistant_index < len(voice_conversation):
                        voice_conversation[voice_current_assistant_index]["content"] = response.content
                        voice_conversation[voice_current_assistant_index]["workflowSteps"] = workflow_steps
                        voice_conversation[voice_current_assistant_index]["timestamp"] = time.time()
                    else:
                        # Fallback: append if placeholder missing
                        voice_conversation.append({
                            "role": "assistant",
                            "content": response.content,
                            "timestamp": time.time(),
                            "workflowSteps": workflow_steps
                        })
                    
                    # Speak the response if TTS is available
                    if hasattr(agent, 'tts_service') and agent.tts_service and agent.tts_service.enabled:
                        print(f"TTS: Speaking response: {response.content[:50]}...")
                        success = agent.tts_service.speak_async(response.content)
                        if not success:
                            print("TTS: Failed to speak, trying fallback...")
                            # Try to create a fallback TTS service with config file API key
                            try:
                                from windows_use.agent.tts_service import TTSService
                                # Get ElevenLabs API key from config file
                                config_file = os.path.join(CONFIG_PATH, "api_keys.json")
                                elevenlabs_key = ""
                                
                                if os.path.exists(config_file):
                                    try:
                                        with open(config_file, "r", encoding="utf-8") as f:
                                            config_data = json.load(f)
                                            elevenlabs_key = config_data.get("elevenlabs_api_key", "")
                                    except:
                                        pass
                                
                                # Set environment variable temporarily for TTS service
                                if elevenlabs_key:
                                    os.environ["ELEVENLABS_API_KEY"] = elevenlabs_key
                                
                                fallback_tts = TTSService(enable_tts=True)
                                if fallback_tts.enabled:
                                    print("TTS: Using fallback TTS service")
                                    fallback_tts.speak_async(response.content)
                                else:
                                    print("TTS: Fallback TTS also not available")
                            except Exception as e:
                                print(f"TTS: Fallback TTS failed: {e}")
                    else:
                        print("TTS: Not available or disabled")
                        # Try to create a fallback TTS service with config file API key
                        try:
                            from windows_use.agent.tts_service import TTSService
                            # Get ElevenLabs API key from config file
                            config_file = os.path.join(CONFIG_PATH, "api_keys.json")
                            elevenlabs_key = ""
                            
                            if os.path.exists(config_file):
                                try:
                                    with open(config_file, "r", encoding="utf-8") as f:
                                        config_data = json.load(f)
                                        elevenlabs_key = config_data.get("elevenlabs_api_key", "")
                                except:
                                    pass
                            
                            # Set environment variable temporarily for TTS service
                            if elevenlabs_key:
                                os.environ["ELEVENLABS_API_KEY"] = elevenlabs_key
                            
                            fallback_tts = TTSService(enable_tts=True)
                            if fallback_tts.enabled:
                                print("TTS: Using fallback TTS service")
                                fallback_tts.speak_async(response.content)
                            else:
                                print("TTS: Fallback TTS also not available")
                        except Exception as e:
                            print(f"TTS: Fallback TTS failed: {e}")
                
            except Exception as e:
                print(f"Error processing voice input: {e}")
            finally:
                # Always release the lock
                _voice_processing_lock = False
                voice_current_assistant_index = None
        
        # Set the callback
        voice_stt_service.on_transcription = on_transcription
        
        # Start listening with proper error handling
        print("[Voice Mode Backend] Starting listening...")
        try:
            # If already listening, treat as idempotent success
            is_listening = getattr(voice_stt_service, 'is_listening', False)
            print(f"[Voice Mode Backend] Current listening status: {is_listening}")
            if is_listening:
                print("[Voice Mode Backend] Already listening, returning success")
                return {"success": True, "message": "Voice mode already started"}
            
            print("[Voice Mode Backend] Calling start_listening()...")
            listening_result = voice_stt_service.start_listening()
            print(f"[Voice Mode Backend] start_listening() returned: {listening_result}")
            
            if listening_result:
                print("[Voice Mode Backend] Successfully started listening")
                return {"success": True, "message": "Voice mode started"}
            else:
                print("[Voice Mode Backend] ERROR: start_listening() returned False")
                raise HTTPException(status_code=500, detail="Failed to start listening")
        except Exception as mic_error:
            print(f"[Voice Mode Backend] ERROR: Microphone access failed: {mic_error}")
            # Clean up the STT service if it was created
            if hasattr(voice_stt_service, 'cleanup'):
                print("[Voice Mode Backend] Cleaning up STT service...")
                voice_stt_service.cleanup()
            raise HTTPException(status_code=500, detail=f"Microphone access failed: {str(mic_error)}")
        
    except Exception as e:
        print(f"[Voice Mode Backend] ERROR: Exception in start_voice_mode: {e}")
        print(f"[Voice Mode Backend] Exception type: {type(e)}")
        import traceback
        print(f"[Voice Mode Backend] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error starting voice mode: {str(e)}")
    finally:
        _voice_starting = False
        print("[Voice Mode Backend] Set _voice_starting to False in finally block")

@app.post("/api/voice/stop")
async def stop_voice_mode():
    """Stop voice mode"""
    print("[Voice Mode Backend] /api/voice/stop endpoint called")
    print(f"[Voice Mode Backend] Agent initialized: {agent_initialized}, Agent exists: {agent is not None}")
    
    if not agent_initialized or not agent:
        print("[Voice Mode Backend] ERROR: Agent not initialized")
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Stop any running voice STT service
        print("[Voice Mode Backend] Checking for STT service...")
        if hasattr(agent, 'stt_service') and agent.stt_service:
            print("[Voice Mode Backend] STT service found, stopping listening...")
            agent.stt_service.stop_listening()
            print("[Voice Mode Backend] Listening stopped, clearing STT service reference")
            agent.stt_service = None
        else:
            print("[Voice Mode Backend] No STT service found")
        
        # Clear voice conversation history and reset processing lock
        global voice_conversation, _voice_processing_lock
        print(f"[Voice Mode Backend] Clearing conversation (length: {len(voice_conversation)}) and resetting lock")
        voice_conversation.clear()
        _voice_processing_lock = False
        
        print("[Voice Mode Backend] Successfully stopped voice mode")
        return {"success": True, "message": "Voice mode stopped"}
        
    except Exception as e:
        print(f"[Voice Mode Backend] ERROR: Exception in stop_voice_mode: {e}")
        import traceback
        print(f"[Voice Mode Backend] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error stopping voice mode: {str(e)}")

@app.get("/api/voice/status")
async def get_voice_status():
    """Get current voice mode status"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        is_listening = False
        is_speaking = False
        
        # Check STT status
        if hasattr(agent, 'stt_service') and agent.stt_service:
            is_listening = agent.stt_service.is_active()
        
        # Check TTS status
        if hasattr(agent, 'is_speaking'):
            is_speaking = agent.is_speaking()
        
        # Check availability (without creating global STT service)
        try:
            from windows_use.agent.stt_service import DEEPGRAM_AVAILABLE
            import os
            # Check if Deepgram API key is available in config file
            stt_available = False
            if DEEPGRAM_AVAILABLE:
                config_file = os.path.join(CONFIG_PATH, "api_keys.json")
                if os.path.exists(config_file):
                    try:
                        with open(config_file, "r", encoding="utf-8") as f:
                            config_data = json.load(f)
                            deepgram_key = config_data.get("deepgram_api_key", "")
                            stt_available = bool(deepgram_key and deepgram_key.strip())
                    except:
                        pass
        except ImportError:
            stt_available = False
        
        # Check if TTS is available based on config file
        tts_available = False
        if hasattr(agent, 'tts_service') and agent.tts_service and agent.tts_service.enabled:
            tts_available = True
        else:
            # Check if ElevenLabs API key is available in config file
            config_file = os.path.join(CONFIG_PATH, "api_keys.json")
            if os.path.exists(config_file):
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        elevenlabs_key = config_data.get("elevenlabs_api_key", "")
                        tts_available = bool(elevenlabs_key and elevenlabs_key.strip())
                except:
                    pass
        
        return {
            "is_listening": is_listening,
            "is_speaking": is_speaking,
            "stt_available": stt_available,
            "tts_available": tts_available
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting voice status: {str(e)}")

@app.get("/api/voice/ready")
async def get_voice_ready():
    """Check if backend is ready to start voice mode (dependencies and keys)."""
    try:
        if not agent_initialized or not agent:
            return {
                "ready": False,
                "reason": "Agent not initialized",
                "details": {"agent_initialized": agent_initialized}
            }

        # STT readiness
        stt_dependency = False
        stt_key_present = False
        stt_reason = None
        try:
            from windows_use.agent.stt_service import DEEPGRAM_AVAILABLE  # type: ignore
            stt_dependency = bool(DEEPGRAM_AVAILABLE)
        except Exception as e:
            stt_reason = f"STT import failed: {e}"

        try:
            config_file = os.path.join(CONFIG_PATH, "api_keys.json")
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    stt_key_present = bool((cfg.get("deepgram_api_key", "") or "").strip())
            else:
                stt_reason = (stt_reason or "") + ("; " if stt_reason else "") + "Config file missing"
        except Exception as e:
            stt_reason = (stt_reason or "") + ("; " if stt_reason else "") + f"Config read error: {e}"

        # TTS readiness
        tts_available = False
        tts_key_present = False
        try:
            if hasattr(agent, 'tts_service') and agent.tts_service and agent.tts_service.enabled:
                tts_available = True
            else:
                config_file = os.path.join(CONFIG_PATH, "api_keys.json")
                if os.path.exists(config_file):
                    with open(config_file, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        tts_key_present = bool((cfg.get("elevenlabs_api_key", "") or "").strip())
        except Exception:
            pass

        ready = stt_dependency and stt_key_present
        return {
            "ready": ready,
            "stt": {
                "dependency": stt_dependency,
                "api_key": stt_key_present,
                "reason": stt_reason
            },
            "tts": {
                "available": tts_available,
                "api_key": tts_key_present
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking voice readiness: {str(e)}")

@app.get("/api/config/keys", response_model=ApiKeysResponse)
async def get_api_keys():
    """Get current API keys from config file"""
    try:
        config_file = os.path.join(CONFIG_PATH, "api_keys.json")
        
        # Load from config file if it exists
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                return ApiKeysResponse(
                    google_api_key=config_data.get("google_api_key", ""),
                    elevenlabs_api_key=config_data.get("elevenlabs_api_key", ""),
                    deepgram_api_key=config_data.get("deepgram_api_key", "")
                )
        else:
            # Return empty keys if config file doesn't exist
            return ApiKeysResponse(
                google_api_key="",
                elevenlabs_api_key="",
                deepgram_api_key=""
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching API keys: {str(e)}")

@app.post("/api/config/keys")
async def save_api_keys(keys: ApiKeysRequest):
    """Save API keys to config file and re-initialize agent"""
    try:
        config_file = os.path.join(CONFIG_PATH, "api_keys.json")
        
        # Create config directory if it doesn't exist
        os.makedirs(CONFIG_PATH, exist_ok=True)
        
        # Prepare config data
        config_data = {
            "google_api_key": keys.google_api_key.strip() if keys.google_api_key else "",
            "elevenlabs_api_key": keys.elevenlabs_api_key.strip() if keys.elevenlabs_api_key else "",
            "deepgram_api_key": keys.deepgram_api_key.strip() if keys.deepgram_api_key else "",
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # Save to config file
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        logger.info("API keys saved, re-initializing agent...")
        
        # Re-initialize agent with new API keys
        success = await initialize_agent()
        
        if success:
            return {
                "success": True,
                "message": "API keys saved and agent initialized successfully."
            }
        else:
            return {
                "success": False,
                "message": "API keys saved, but agent initialization failed. Please check your API keys."
            }
    except Exception as e:
        logger.error(f"Error saving API keys: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving API keys: {str(e)}")

# Scheduled Tasks API
class CreateTaskRequest(BaseModel):
    name: Optional[str] = None
    query: Optional[str] = None
    delay_seconds: Optional[int] = None
    run_at: Optional[str] = None

class UpdateTaskRequest(BaseModel):
    name: Optional[str] = None
    query: Optional[str] = None
    delay_seconds: Optional[int] = None
    run_at: Optional[str] = None
    status: Optional[str] = None  # allow cancel

@app.get("/api/scheduled-tasks", response_model=List[ScheduledTask])
async def list_scheduled_tasks():
    with _scheduled_lock:
        return list(_scheduled_tasks.values())

@app.post("/api/scheduled-tasks", response_model=ScheduledTask)
async def create_scheduled_task(req: CreateTaskRequest):
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    delay_seconds = req.delay_seconds
    run_at = (req.run_at or '').strip() if req.run_at else None
    # If no explicit scheduling provided, try to parse from query
    if (delay_seconds is None) and (not run_at or not run_at.strip()):
        if req.query and req.query.strip():
            parsed_delay, parsed_run_at = _extract_time_from_text(req.query)
            delay_seconds = parsed_delay
            run_at = parsed_run_at
        if (delay_seconds is None) and (not run_at or not run_at.strip()):
            raise HTTPException(status_code=400, detail="Provide delay_seconds/run_at or include timing in the query (e.g., 'in 20 minutes' or 'at 10:30 am')")
    if (not req.name or not req.name.strip()) and (not req.query or not req.query.strip()):
        raise HTTPException(status_code=400, detail="Provide a name or a query for the task")
    # compute scheduled_for for display
    scheduled_for = None
    if run_at and run_at.strip():
        scheduled_for = run_at.strip()
    created = datetime.now().isoformat()
    task_id = str(uuid.uuid4())
    task = ScheduledTask(
        id=task_id,
        name=req.name.strip() if req.name else None,
        query=req.query.strip() if req.query else None,
        delay_seconds=delay_seconds,
        run_at=run_at,
        status="scheduled",
        created_at=created,
        scheduled_for=scheduled_for
    )
    with _scheduled_lock:
        _scheduled_tasks[task_id] = task
        _persist_scheduled_tasks()
    _schedule_timer_for_task(task)
    return task

@app.patch("/api/scheduled-tasks/{task_id}", response_model=ScheduledTask)
async def update_scheduled_task(task_id: str, req: UpdateTaskRequest):
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    with _scheduled_lock:
        task = _scheduled_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if req.name is not None:
            task.name = req.name
        if req.query is not None:
            task.query = req.query
        if req.delay_seconds is not None or (req.run_at is not None):
            task.delay_seconds = req.delay_seconds
            task.run_at = req.run_at.strip() if req.run_at else None
            task.status = "scheduled"
        if req.status == "cancelled":
            task.status = "cancelled"
            timer = _scheduled_timers.pop(task_id, None)
            if timer:
                try:
                    timer.cancel()
                except Exception:
                    pass
        # recompute scheduled_for
        task.scheduled_for = task.run_at if task.run_at else None
        _scheduled_tasks[task_id] = task
        _persist_scheduled_tasks()
    # if re-scheduled and not cancelled, set a new timer
    if task.status == "scheduled":
        _schedule_timer_for_task(task)
    return task

@app.delete("/api/scheduled-tasks/{task_id}")
async def delete_scheduled_task(task_id: str):
    with _scheduled_lock:
        if task_id not in _scheduled_tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        timer = _scheduled_timers.pop(task_id, None)
        if timer:
            try:
                timer.cancel()
            except Exception:
                pass
        del _scheduled_tasks[task_id]
        _persist_scheduled_tasks()
    return {"success": True}

@app.post("/api/scheduled-tasks/{task_id}/repeat", response_model=ScheduledTask)
async def repeat_scheduled_task(task_id: str):
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    with _scheduled_lock:
        original = _scheduled_tasks.get(task_id)
        if not original:
            raise HTTPException(status_code=404, detail="Task not found")
        # Determine next schedule: if run_at present, reuse same time (advance to next day if needed); else reuse delay_seconds
        new_run_at = original.run_at
        new_delay = original.delay_seconds
        if original.run_at:
            # if time today has passed, parser in _parse_run_at_to_delay already advances; we keep same string
            pass
        new_task = ScheduledTask(
            id=str(uuid.uuid4()),
            name=original.name,
            query=original.query,
            delay_seconds=new_delay,
            run_at=new_run_at,
            status="scheduled",
            created_at=datetime.now().isoformat(),
            scheduled_for=new_run_at
        )
        _scheduled_tasks[new_task.id] = new_task
        _persist_scheduled_tasks()
    _schedule_timer_for_task(new_task)
    return new_task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
