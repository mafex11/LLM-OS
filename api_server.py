"""
FastAPI Server for Yuki AI Agent
Provides REST API endpoints for the Next.js frontend
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional
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

VALID_GEMINI_MODELS: List[str] = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]
DEFAULT_GEMINI_MODEL: str = "gemini-2.0-flash"

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
                "version": "1.0",
                "model": DEFAULT_GEMINI_MODEL
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
            pending = []
            for task in list(_scheduled_tasks.values()):
                if task.status in ("scheduled", "running"):
                    task.status = "scheduled"
                    _scheduled_tasks[task.id] = task
                    pending.append(task)
            if pending:
                _persist_scheduled_tasks()
        for task in pending:
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

# Notification queue for activity tracking notifications
_notification_queue: List[Dict[str, str]] = []
_notification_lock = threading.Lock()

def handle_notification(title: str, message: str):
    """Handle notification from activity tracker."""
    with _notification_lock:
        _notification_queue.append({
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 100 notifications
        if len(_notification_queue) > 100:
            _notification_queue.pop(0)
    logger.info(f"Notification queued: {title} - {message}")

# Function to initialize the agent (can be called multiple times)
async def initialize_agent():
    """Initialize or re-initialize the agent with current API keys"""
    global agent, streaming_wrapper, agent_initialized
    
    try:
        logger.info("Starting agent initialization...")
        print("Initializing Yuki AI Agent...")
        
        # Get Google API key from config file
        config_file = os.path.join(CONFIG_PATH, "api_keys.json")
        config_data: Dict[str, Any] = {}
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
                config_data = {}
        else:
            logger.warning(f"Config file not found: {config_file}")
            print(f"⚠️  Config file not found: {config_file}")
        
        if not google_api_key or not google_api_key.strip():
            error_msg = "Google API key is not set. Please configure it in the settings page."
            logger.error(error_msg)
            print(f"🚨 {error_msg}")
            agent_initialized = False
            return False
        
        model_setting = DEFAULT_GEMINI_MODEL
        if config_data:
            model_setting = config_data.get("model", DEFAULT_GEMINI_MODEL)
        if model_setting not in VALID_GEMINI_MODELS:
            logger.warning(f"Requested model '{model_setting}' is not supported. Falling back to default.")
            model_setting = DEFAULT_GEMINI_MODEL

        logger.info(f"Initializing ChatGoogleGenerativeAI with model: {model_setting}")
        llm = ChatGoogleGenerativeAI(
            model=model_setting,
            temperature=0.3,
            google_api_key=google_api_key
        )
        logger.info("ChatGoogleGenerativeAI initialized successfully")
        
        # TTS configuration - check if ElevenLabs API key is available
        enable_tts = False
        tts_voice_id = config_data.get("tts_voice_id", "21m00Tcm4TlvDq8ikWAM")
        
        logger.info("Checking TTS configuration...")
        elevenlabs_key = config_data.get("elevenlabs_api_key", "")
        enable_tts_setting = bool(config_data.get("enable_tts", False))
        if enable_tts_setting and elevenlabs_key and elevenlabs_key.strip():
            enable_tts = True
            logger.info("ElevenLabs API key found, TTS enabled")
        elif enable_tts_setting:
            enable_tts = False
            logger.info("TTS enabled in settings but ElevenLabs API key missing. TTS will remain disabled.")
        else:
            logger.info("TTS disabled in settings")
        
        # Set notification callback before initializing agent (so it's available during tracking init)
        # Create agent with notification callback
        logger.info("Initializing Agent with parameters...")
        
        # Load agent settings from config file if available
        enable_screenshot_analysis = config_data.get("enable_screenshot_analysis", True)
        enable_activity_tracking = config_data.get("enable_activity_tracking", True)
        enable_vision = config_data.get("enable_vision", False)
        enable_conversation = config_data.get("enable_conversation", True)
        max_steps_setting = int(config_data.get("max_steps", 100) or 100)
        literal_mode_setting = bool(config_data.get("literal_mode", True))
        browser_setting = config_data.get("browser", "chrome")
        consecutive_failures_setting = int(config_data.get("consecutive_failures", 3) or 3)
        cache_timeout_setting = float(config_data.get("cache_timeout", 2.0) or 2.0)
        
        # Sanitize configurable values
        if browser_setting not in ("edge", "chrome", "firefox"):
            browser_setting = "chrome"
        max_steps_setting = max(1, min(200, max_steps_setting))
        consecutive_failures_setting = max(1, min(10, consecutive_failures_setting))
        cache_timeout_setting = max(0.1, min(10.0, cache_timeout_setting))
        
        # Create agent instance
        agent_instance = Agent(
            llm=llm,
            browser=browser_setting,
            use_vision=enable_vision,
            enable_conversation=enable_conversation,
            literal_mode=literal_mode_setting,
            max_steps=max_steps_setting,
            consecutive_failures=consecutive_failures_setting,
            enable_tts=enable_tts,
            tts_voice_id=tts_voice_id,
            enable_screenshot_analysis=enable_screenshot_analysis,
            enable_activity_tracking=enable_activity_tracking
        )
        agent_instance.model_id = model_setting
        agent_instance.desktop.cache_timeout = cache_timeout_setting
        
        # Set notification callback (tracking is initialized in __init__, so we need to set it after)
        agent_instance.notification_callback = handle_notification
        
        # Update notification service with callback and LLM if tracking is already initialized
        if agent_instance.activity_tracker and hasattr(agent_instance.activity_tracker, 'notification_service'):
            agent_instance.activity_tracker.notification_service.set_notification_callback(handle_notification)
            # Ensure LLM is available for AI classification
            if llm and hasattr(agent_instance.activity_tracker.notification_service, 'set_llm'):
                agent_instance.activity_tracker.notification_service.set_llm(llm)
            # Also set activity analyzer if available
            if agent_instance.activity_analyzer and hasattr(agent_instance.activity_tracker.notification_service, 'set_activity_analyzer'):
                agent_instance.activity_tracker.notification_service.set_activity_analyzer(agent_instance.activity_analyzer)
            logger.info("Notification callback and AI support set on activity tracker")
        else:
            # If tracking hasn't been initialized yet, the callback will be used when it is
            logger.info("Notification callback stored for when tracking initializes")
        
        agent = agent_instance
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
        
        # Ensure notification callback and AI are set (in case tracking was initialized)
        if hasattr(agent, 'activity_tracker') and agent.activity_tracker:
            if hasattr(agent.activity_tracker, 'notification_service'):
                agent.activity_tracker.notification_service.set_notification_callback(handle_notification)
                # Ensure LLM is available for AI classification
                if llm and hasattr(agent.activity_tracker.notification_service, 'set_llm'):
                    agent.activity_tracker.notification_service.set_llm(llm)
                # Also set activity analyzer if available
                if hasattr(agent, 'activity_analyzer') and agent.activity_analyzer:
                    if hasattr(agent.activity_tracker.notification_service, 'set_activity_analyzer'):
                        agent.activity_tracker.notification_service.set_activity_analyzer(agent.activity_analyzer)
                logger.info("Notification callback and AI support registered for activity tracker")
        
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
    consecutive_failures: int = 3
    browser: Literal["edge", "chrome", "firefox"] = "chrome"
    literal_mode: bool = True
    model: Literal[
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ] = DEFAULT_GEMINI_MODEL
    enable_screenshot_analysis: bool = True
    enable_activity_tracking: bool = True
    enable_vision: bool = False
    enable_conversation: bool = True

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
    repeat: Optional[str] = None  # none, daily, weekly, interval
    days_of_week: Optional[List[int]] = None  # 0=Monday ... 6=Sunday
    last_run_at: Optional[str] = None
    last_run_status: Optional[str] = None
    repeat_interval_seconds: Optional[int] = None  # Interval in seconds (e.g., 600 for 10 minutes, 7200 for 2 hours)
    repeat_end_time: Optional[str] = None  # HH:MM format - stop repeating after this time in the day

# In-memory registry and persistence for scheduled tasks
_scheduled_tasks: Dict[str, ScheduledTask] = {}
_scheduled_timers: Dict[str, threading.Timer] = {}
_scheduled_lock = threading.Lock()
SCHEDULED_TASKS_FILE = os.path.join(DATA_PATH, "scheduled_tasks.json")

def _normalize_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    try_text = text.replace("Z", "+00:00") if text.endswith("Z") else text
    try:
        dt = datetime.fromisoformat(try_text)
    except ValueError:
        return None
    if dt.tzinfo:
        return dt.astimezone().replace(tzinfo=None)
    return dt


def _is_time_only(text: str) -> bool:
    if not text:
        return False
    lowered = text.strip().lower()
    return bool(re.fullmatch(r"\d{1,2}:\d{2}(?::\d{2})?\s*(am|pm)?", lowered))


def _parse_time_of_day_components(value: Optional[str]) -> Optional[tuple[int, int, int]]:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    dt = _normalize_iso_datetime(text)
    if dt:
        return dt.hour, dt.minute, dt.second
    match = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?(?::(\d{2}))?\s*(am|pm)?", text.lower())
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    second = int(match.group(3) or 0)
    period = match.group(4)
    if period:
        hour = hour % 12 + (12 if period == "pm" else 0)
    if hour >= 24 or minute >= 60 or second >= 60:
        return None
    return hour, minute, second


def _resolve_run_datetime(run_at: Optional[str], base: datetime, allow_rollover: bool) -> Optional[datetime]:
    if not run_at:
        return None
    direct = _normalize_iso_datetime(run_at)
    if direct:
        if direct <= base and not allow_rollover:
            return None
        if direct <= base and allow_rollover:
            # advance by whole days until future
            delta_days = int(((base - direct).total_seconds() // 86400) + 1)
            direct = direct + timedelta(days=max(1, delta_days))
        return direct
    components = _parse_time_of_day_components(run_at)
    if not components:
        return None
    candidate = base.replace(
        hour=components[0],
        minute=components[1],
        second=components[2],
        microsecond=0,
    )
    if allow_rollover and candidate <= base:
        candidate += timedelta(days=1)
    if candidate <= base and not allow_rollover:
        return None
    return candidate


def _should_repeat(task: ScheduledTask) -> bool:
    repeat = (task.repeat or "").strip().lower()
    # Check for interval-based repeats
    if task.repeat_interval_seconds and task.repeat_interval_seconds > 0:
        return True
    # Check for daily/weekly repeats
    return bool(repeat in {"daily", "weekly"} or (task.days_of_week and len(task.days_of_week) > 0))


def _compute_next_run_datetime(task: ScheduledTask, reference: Optional[datetime] = None) -> Optional[datetime]:
    ref = (reference or datetime.now()).replace(microsecond=0)
    repeat = (task.repeat or "").strip().lower()
    days = sorted({int(d) % 7 for d in (task.days_of_week or [])}) if task.days_of_week else []
    if repeat == "daily" and not days:
        days = list(range(7))
    if repeat == "weekly" and not days:
        days = list(range(7))
    if repeat in {"daily", "weekly"} or days:
        components = _parse_time_of_day_components(task.run_at)
        if not components:
            return None
        start_date = ref.date()
        # search up to 14 days ahead to find next valid slot
        for offset in range(0, 14):
            candidate_date = start_date + timedelta(days=offset)
            if days and candidate_date.weekday() not in days:
                continue
            candidate = datetime.combine(candidate_date, datetime.min.time()).replace(
                hour=components[0],
                minute=components[1],
                second=components[2],
                microsecond=0,
            )
            if candidate <= ref:
                continue
            return candidate
        return None
    # Handle interval-based repeats (e.g., every 10 minutes, every 2 hours)
    if task.repeat_interval_seconds and task.repeat_interval_seconds > 0:
        # Determine base time for calculating next run
        base_time = None
        
        # If this is a repeat run, use last_run_at
        if task.last_run_at:
            base_time = _normalize_iso_datetime(task.last_run_at)
        
        # If no last_run_at, this is the first run - determine start time
        if not base_time:
            if task.run_at:
                # Use run_at as start time
                start_components = _parse_time_of_day_components(task.run_at)
                if start_components:
                    today = ref.date()
                    base_time = datetime.combine(today, datetime.min.time()).replace(
                        hour=start_components[0],
                        minute=start_components[1],
                        second=start_components[2],
                        microsecond=0,
                    )
                    # If start time is in the past today, use it for today anyway (will be adjusted below)
                    if base_time < ref:
                        # Start immediately or use current time
                        base_time = ref
            elif task.delay_seconds is not None:
                # Use delay_seconds from creation time
                created = _normalize_iso_datetime(task.created_at) or ref
                base_time = created + timedelta(seconds=task.delay_seconds)
            else:
                # Start immediately
                base_time = ref
        
        # Calculate next run time
        next_run = base_time + timedelta(seconds=task.repeat_interval_seconds)
        
        # Parse end time if set (HH:MM format)
        end_time_components = None
        if task.repeat_end_time:
            end_time_components = _parse_time_of_day_components(task.repeat_end_time)
        
        # Check constraints: end time and day boundaries
        next_run_date = next_run.date()
        base_date = base_time.date()
        
        # Check if we've crossed to a new day
        if next_run_date > base_date:
            # Crossed to next day - check if we should continue
            if task.run_at:
                # Restart at run_at time on next day
                start_components = _parse_time_of_day_components(task.run_at)
                if start_components:
                    next_run = datetime.combine(next_run_date, datetime.min.time()).replace(
                        hour=start_components[0],
                        minute=start_components[1],
                        second=start_components[2],
                        microsecond=0,
                    )
                else:
                    # Invalid start time - stop
                    return None
            elif end_time_components:
                # Check if next run time on next day is past end time
                end_time_next_day = datetime.combine(next_run_date, datetime.min.time()).replace(
                    hour=end_time_components[0],
                    minute=end_time_components[1],
                    second=end_time_components[2],
                    microsecond=0,
                )
                if next_run > end_time_next_day:
                    # Past end time on next day - stop (no start time to restart)
                    return None
            # If no end time and no start time, continue with calculated time
        
        # Check end time constraint on same day
        if end_time_components and next_run_date == base_date:
            end_time_today = datetime.combine(base_date, datetime.min.time()).replace(
                hour=end_time_components[0],
                minute=end_time_components[1],
                second=end_time_components[2],
                microsecond=0,
            )
            if next_run > end_time_today:
                # Past end time - schedule for next day at start time (if available)
                if task.run_at:
                    start_components = _parse_time_of_day_components(task.run_at)
                    if start_components:
                        next_day = base_date + timedelta(days=1)
                        next_run = datetime.combine(next_day, datetime.min.time()).replace(
                            hour=start_components[0],
                            minute=start_components[1],
                            second=start_components[2],
                            microsecond=0,
                        )
                    else:
                        return None
                else:
                    # No start time - stop repeating
                    return None
        
        # Ensure next run is in the future (at least ref time)
        if next_run < ref:
            # Calculate from ref instead
            next_run = ref + timedelta(seconds=task.repeat_interval_seconds)
            # Re-check constraints
            if end_time_components and next_run.date() == ref.date():
                end_time_today = datetime.combine(ref.date(), datetime.min.time()).replace(
                    hour=end_time_components[0],
                    minute=end_time_components[1],
                    second=end_time_components[2],
                    microsecond=0,
                )
                if next_run > end_time_today:
                    if task.run_at:
                        start_components = _parse_time_of_day_components(task.run_at)
                        if start_components:
                            next_day = ref.date() + timedelta(days=1)
                            next_run = datetime.combine(next_day, datetime.min.time()).replace(
                                hour=start_components[0],
                                minute=start_components[1],
                                second=start_components[2],
                                microsecond=0,
                            )
                        else:
                            return None
                    else:
                        return None
        
        return next_run
    if task.delay_seconds is not None:
        created = _normalize_iso_datetime(task.created_at) or ref
        target = created + timedelta(seconds=int(task.delay_seconds))
        if target <= ref:
            return ref
        return target
    if task.run_at:
        allow_roll = _is_time_only(task.run_at)
        return _resolve_run_datetime(task.run_at, ref, allow_roll)
    return None


def _parse_run_at_to_delay(run_at_text: str) -> Optional[float]:
    text = (run_at_text or "").strip()
    if not text:
        return None
    now = datetime.now().replace(microsecond=0)
    allow_roll = _is_time_only(text)
    dt = _resolve_run_datetime(text, now, allow_roll)
    if not dt:
        return None
    return max(0.0, (dt - now).total_seconds())


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
    now = datetime.now().replace(microsecond=0)
    with _scheduled_lock:
        stored = _scheduled_tasks.get(task.id)
        if not stored:
            return
        next_run = _normalize_iso_datetime(stored.scheduled_for)
        if not next_run or next_run <= now:
            next_run = _compute_next_run_datetime(stored, reference=now)
        if not next_run:
            stored.status = "failed"
            stored.last_error = "Invalid schedule time"
            _scheduled_tasks[task.id] = stored
            _persist_scheduled_tasks()
            return
        stored.scheduled_for = next_run.isoformat()
        if stored.status not in {"running", "completed", "failed", "cancelled"}:
            stored.status = "scheduled"
        _scheduled_tasks[task.id] = stored
        _persist_scheduled_tasks()
        old_timer = _scheduled_timers.pop(task.id, None)
    if old_timer:
        try:
            old_timer.cancel()
        except Exception:
            pass

    delay = max(0.0, (next_run - now).total_seconds())

    def _run():
        status_code = 0
        response_message = ""
        with _scheduled_lock:
            current = _scheduled_tasks.get(task.id)
            _scheduled_timers.pop(task.id, None)
            if not current or current.status == "cancelled":
                return
            current.status = "running"
            _scheduled_tasks[task.id] = current
            _persist_scheduled_tasks()
        try:
            if current.query and current.query.strip():
                try:
                    agent.invoke(current.query)
                except Exception as e:
                    status_code = 1
                    response_message = str(e)
            elif current.name:
                app_name, response_message, launch_status = agent.desktop.launch_app(current.name)
                if launch_status != 0:
                    status_code = launch_status or 1
                else:
                    try:
                        if app_name:
                            agent.desktop.switch_app(app_name)
                    except Exception:
                        pass
            else:
                status_code = 1
                response_message = "Task missing name or query"
        except Exception as e:
            status_code = 1
            response_message = str(e)
        finally:
            finished_at = datetime.now().replace(microsecond=0)
            reschedule = False
            task_snapshot: Optional[ScheduledTask] = None
            with _scheduled_lock:
                current = _scheduled_tasks.get(task.id)
                if not current:
                    return
                current.last_run_at = finished_at.isoformat()
                if status_code == 0:
                    current.last_error = None
                    current.last_run_status = "completed"
                else:
                    current.last_error = response_message
                    current.last_run_status = "failed"
                if current.status == "cancelled":
                    _scheduled_tasks[task.id] = current
                    _persist_scheduled_tasks()
                    return
                if _should_repeat(current):
                    current.status = "scheduled"
                    current.scheduled_for = None
                    _scheduled_tasks[task.id] = current
                    _persist_scheduled_tasks()
                    reschedule = True
                    task_snapshot = current
                else:
                    current.status = "completed" if status_code == 0 else "failed"
                    current.scheduled_for = None
                    _scheduled_tasks[task.id] = current
                    _persist_scheduled_tasks()
            if reschedule and task_snapshot:
                _schedule_timer_for_task(task_snapshot)

    timer = threading.Timer(delay, _run)
    timer.daemon = True
    with _scheduled_lock:
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
            current_model = getattr(agent, 'model_id', DEFAULT_GEMINI_MODEL)
            if current_model not in VALID_GEMINI_MODELS:
                current_model = DEFAULT_GEMINI_MODEL
            llm = ChatGoogleGenerativeAI(
                model=current_model, 
                temperature=0.3,
                google_api_key=google_api_key
            )
            
            # Create a new agent instance with the frontend API key
            frontend_agent = Agent(
                llm=llm,
                browser=getattr(agent, 'browser', 'chrome'),
                use_vision=request.use_vision and getattr(agent, 'use_vision', False),
                enable_conversation=getattr(agent, 'enable_conversation', True),
                literal_mode=getattr(agent, 'literal_mode', True),
                max_steps=getattr(agent, 'max_steps', 50),
                consecutive_failures=getattr(agent, 'consecutive_failures', 3),
                enable_screenshot_analysis=getattr(agent, 'enable_screenshot_analysis', True),
                enable_activity_tracking=getattr(agent, 'enable_activity_tracking', True),
                enable_tts=False,  # We'll handle TTS separately
                tts_voice_id=getattr(agent, 'tts_voice_id', "21m00Tcm4TlvDq8ikWAM")
            )
            frontend_agent.model_id = current_model
            if hasattr(frontend_agent, 'desktop'):
                frontend_agent.desktop.cache_timeout = getattr(agent.desktop, 'cache_timeout', 2.0) if hasattr(agent, 'desktop') else 2.0
            
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

# Get current settings
@app.get("/api/settings")
async def get_settings():
    """Get current agent settings"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        settings = {
            "enable_tts": getattr(agent, 'enable_tts', False),
            "tts_voice_id": getattr(agent, 'tts_voice_id', "21m00Tcm4TlvDq8ikWAM"),
            "cache_timeout": getattr(agent.desktop, 'cache_timeout', 2.0) if hasattr(agent, 'desktop') else 2.0,
            "max_steps": getattr(agent, 'max_steps', 50),
            "consecutive_failures": getattr(agent, 'consecutive_failures', 3),
            "browser": getattr(agent, 'browser', "chrome"),
            "literal_mode": getattr(agent, 'literal_mode', True),
            "model": getattr(agent, 'model_id', getattr(getattr(agent, 'llm', None), 'model', DEFAULT_GEMINI_MODEL)),
            "enable_screenshot_analysis": getattr(agent, 'enable_screenshot_analysis', True),
            "enable_activity_tracking": getattr(agent, 'enable_activity_tracking', True),
            "enable_vision": getattr(agent, 'use_vision', False),
            "enable_conversation": getattr(agent, 'enable_conversation', True)
        }
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting settings: {str(e)}")

# Update settings
@app.post("/api/settings")
async def update_settings(request: SettingsRequest):
    """Update agent settings"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        bounded_max_steps = max(1, min(200, request.max_steps))
        bounded_cache_timeout = max(0.1, min(10.0, request.cache_timeout))
        bounded_consecutive_failures = max(1, min(10, request.consecutive_failures))
        if request.model not in VALID_GEMINI_MODELS:
            raise HTTPException(status_code=400, detail=f"Unsupported model: {request.model}")

        config_file = os.path.join(CONFIG_PATH, "api_keys.json")
        config_data: Dict[str, Any] = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception as read_error:
                logger.warning(f"Failed to read config file before updating settings: {read_error}")
                config_data = {}

        previous_browser = getattr(agent, 'browser', request.browser)
        previous_literal_mode = getattr(agent, 'literal_mode', request.literal_mode)
        previous_max_steps = getattr(agent, 'max_steps', bounded_max_steps)
        previous_model = getattr(agent, 'model_id', DEFAULT_GEMINI_MODEL)
        model_changed = previous_model != request.model
        should_reset_prompt = (
            previous_browser != request.browser
            or previous_literal_mode != request.literal_mode
            or previous_max_steps != bounded_max_steps
            or model_changed
        )

        # Update TTS settings
        tts_service = getattr(agent, 'tts_service', None)
        if request.enable_tts:
            if tts_service:
                tts_service.enabled = True
                tts_service.voice_id = request.tts_voice_id
            else:
                try:
                    from windows_use.agent.tts_service import TTSService
                    agent.tts_service = TTSService(voice_id=request.tts_voice_id, enable_tts=True)
                except Exception as tts_error:
                    logger.warning(f"Failed to initialize TTS service: {tts_error}")
        else:
            if tts_service:
                tts_service.enabled = False
                try:
                    tts_service.stop_current_speech()
                except Exception:
                    pass
        
        # Update agent TTS flags
        agent.enable_tts = request.enable_tts
        agent.tts_voice_id = request.tts_voice_id
        
        # Update browser and literal mode
        agent.browser = request.browser
        agent.literal_mode = request.literal_mode
        agent.model_id = request.model
        
        # Update cache timeout
        if hasattr(agent, 'desktop'):
            agent.desktop.cache_timeout = bounded_cache_timeout
        
        # Update max steps
        agent.max_steps = bounded_max_steps
        
        # Update consecutive failure limit
        agent.consecutive_failures = bounded_consecutive_failures
        
        # Update vision mode
        agent.use_vision = request.enable_vision
        
        # Update conversation mode
        agent.enable_conversation = request.enable_conversation
        if not request.enable_conversation and hasattr(agent, 'conversation_history'):
            try:
                agent.conversation_history.clear()
            except Exception:
                agent.conversation_history = []
        
        # Update screenshot analysis and activity tracking
        screenshot_analysis_changed = getattr(agent, 'enable_screenshot_analysis', True) != request.enable_screenshot_analysis
        activity_tracking_changed = getattr(agent, 'enable_activity_tracking', True) != request.enable_activity_tracking
        
        agent.enable_screenshot_analysis = request.enable_screenshot_analysis
        agent.enable_activity_tracking = request.enable_activity_tracking
        
        # If screenshot analysis or activity tracking changed, reinitialize tracking
        if screenshot_analysis_changed or activity_tracking_changed:
            # Stop existing tracking if running
            if hasattr(agent, 'activity_tracker') and agent.activity_tracker:
                try:
                    agent.activity_tracker.stop_tracking()
                except Exception as e:
                    logger.warning(f"Error stopping activity tracker: {e}")
            
            if hasattr(agent, 'screenshot_service') and agent.screenshot_service:
                try:
                    agent.screenshot_service.stop_capturing()
                except Exception as e:
                    logger.warning(f"Error stopping screenshot service: {e}")
            
            # Reinitialize tracking with new settings
            agent._initialize_tracking()
            logger.info(f"Activity tracking reinitialized (screenshot analysis: {request.enable_screenshot_analysis}, activity tracking: {request.enable_activity_tracking})")
        
        # Reset system prompt when core planning parameters change
        if should_reset_prompt and hasattr(agent, 'system_message'):
            agent.system_message = None
        
        # Reinitialize LLM if model changed and API key available
        try:
            google_api_key = config_data.get("google_api_key", "")
            if model_changed and google_api_key:
                temperature = getattr(agent.llm, "temperature", 0.3) if hasattr(agent, "llm") else 0.3
                agent.llm = ChatGoogleGenerativeAI(
                    model=request.model,
                    temperature=temperature,
                    google_api_key=google_api_key,
                )
                logger.info(f"Agent language model updated to {request.model}")
            elif model_changed and not google_api_key:
                logger.warning("Cannot update language model because Google API key is missing.")
        except Exception as llm_error:
            logger.warning(f"Failed to update language model: {llm_error}")
        
        # Save settings to config file for persistence
        try:
            # Update agent settings in config
            config_data["enable_screenshot_analysis"] = request.enable_screenshot_analysis
            config_data["enable_activity_tracking"] = request.enable_activity_tracking
            config_data["enable_vision"] = request.enable_vision
            config_data["enable_conversation"] = request.enable_conversation
            config_data["max_steps"] = bounded_max_steps
            config_data["cache_timeout"] = bounded_cache_timeout
            config_data["enable_tts"] = request.enable_tts
            config_data["tts_voice_id"] = request.tts_voice_id
            config_data["consecutive_failures"] = bounded_consecutive_failures
            config_data["browser"] = request.browser
            config_data["literal_mode"] = request.literal_mode
            config_data["model"] = request.model
            
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            logger.info("Agent settings saved to config file")
        except Exception as e:
            logger.warning(f"Failed to save settings to config file: {e}")
        
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

VALID_GEMINI_MODELS: List[str] = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]
DEFAULT_GEMINI_MODEL: str = "gemini-2.0-flash"

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
            
            # Check conversation mode status
            in_conversation_mode = voice_stt_service.is_in_conversation_mode() if hasattr(voice_stt_service, 'is_in_conversation_mode') else False
            
            # Check if we're waiting for a command after trigger word detection
            if voice_stt_service.is_waiting_for_command():
                print(f"Voice command received: {transcript}")
            elif in_conversation_mode:
                print(f"Query received in conversation mode: {transcript}")
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
        
        # Read existing config to preserve agent settings
        config_data = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception as e:
                logger.warning(f"Error reading existing config file: {e}")
                config_data = {}
        
        # Update only API keys, preserve all other settings
        config_data["google_api_key"] = keys.google_api_key.strip() if keys.google_api_key else ""
        config_data["elevenlabs_api_key"] = keys.elevenlabs_api_key.strip() if keys.elevenlabs_api_key else ""
        config_data["deepgram_api_key"] = keys.deepgram_api_key.strip() if keys.deepgram_api_key else ""
        config_data["last_updated"] = datetime.now().isoformat()
        if "version" not in config_data:
            config_data["version"] = "1.0"
        
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
    repeat: Optional[str] = None
    days_of_week: Optional[List[int]] = None
    repeat_interval_seconds: Optional[int] = None  # Interval in seconds for interval-based repeats
    repeat_end_time: Optional[str] = None  # HH:MM format - stop repeating after this time

class UpdateTaskRequest(BaseModel):
    name: Optional[str] = None
    query: Optional[str] = None
    delay_seconds: Optional[int] = None
    run_at: Optional[str] = None
    status: Optional[str] = None  # allow cancel
    repeat: Optional[str] = None
    days_of_week: Optional[List[int]] = None
    repeat_interval_seconds: Optional[int] = None  # Interval in seconds for interval-based repeats
    repeat_end_time: Optional[str] = None  # HH:MM format - stop repeating after this time

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
    repeat_value = (req.repeat or '').strip().lower() if req.repeat else None
    
    # Handle interval-based repeats
    repeat_interval_seconds = req.repeat_interval_seconds
    repeat_end_time = (req.repeat_end_time or '').strip() if req.repeat_end_time else None
    
    # Validate interval-based repeat fields
    if repeat_interval_seconds is not None:
        if repeat_interval_seconds <= 0:
            raise HTTPException(status_code=400, detail="repeat_interval_seconds must be positive")
        # Set repeat to "interval" if interval is provided
        if not repeat_value:
            repeat_value = "interval"
        elif repeat_value not in {"interval", "daily", "weekly"}:
            raise HTTPException(status_code=400, detail="Cannot combine interval-based repeat with daily/weekly repeat")
    
    # Validate end time format if provided
    if repeat_end_time:
        if not _parse_time_of_day_components(repeat_end_time):
            raise HTTPException(status_code=400, detail="repeat_end_time must be in HH:MM format")
    
    if repeat_value and repeat_value not in {"daily", "weekly", "interval"}:
        raise HTTPException(status_code=400, detail="Repeat must be 'daily', 'weekly', or 'interval'")
    if repeat_value and repeat_value != "interval" and delay_seconds is not None:
        raise HTTPException(status_code=400, detail="Repeat schedules use run_at, not delay_seconds")
    days_normalized: Optional[List[int]] = None
    if req.days_of_week is not None:
        try:
            cleaned = sorted({int(d) % 7 for d in req.days_of_week})
        except Exception:
            raise HTTPException(status_code=400, detail="days_of_week must be integers between 0 and 6")
        if any(d < 0 or d > 6 for d in cleaned):
            raise HTTPException(status_code=400, detail="days_of_week entries must be between 0 (Monday) and 6 (Sunday)")
        days_normalized = cleaned or None
    if repeat_value and repeat_value != "interval":
        if not run_at:
            raise HTTPException(status_code=400, detail="Repeat schedules require run_at")
        if repeat_value == "weekly" and not days_normalized:
            raise HTTPException(status_code=400, detail="Weekly repeat requires days_of_week")
    # If no explicit scheduling provided and not interval-based, try to parse from query
    if repeat_value != "interval" and (delay_seconds is None) and (not run_at or not run_at.strip()):
        if req.query and req.query.strip():
            parsed_delay, parsed_run_at = _extract_time_from_text(req.query)
            delay_seconds = parsed_delay
            run_at = parsed_run_at
        if (delay_seconds is None) and (not run_at or not run_at.strip()):
            raise HTTPException(status_code=400, detail="Provide delay_seconds/run_at or include timing in the query (e.g., 'in 20 minutes' or 'at 10:30 am')")
    if (not req.name or not req.name.strip()) and (not req.query or not req.query.strip()):
        raise HTTPException(status_code=400, detail="Provide a name or a query for the task")
    created_dt = datetime.now().replace(microsecond=0)
    created = created_dt.isoformat()
    if repeat_value and repeat_value != "interval":
        delay_seconds = None
    # For interval-based repeats, delay_seconds can be used for initial delay
    task_id = str(uuid.uuid4())
    task = ScheduledTask(
        id=task_id,
        name=req.name.strip() if req.name else None,
        query=req.query.strip() if req.query else None,
        delay_seconds=delay_seconds,
        run_at=run_at,
        status="scheduled",
        created_at=created,
        scheduled_for=None,
        repeat=repeat_value,
        days_of_week=days_normalized,
        last_run_at=None,
        last_run_status=None,
        repeat_interval_seconds=repeat_interval_seconds,
        repeat_end_time=repeat_end_time
    )
    next_run = _compute_next_run_datetime(task)
    if not next_run:
        raise HTTPException(status_code=400, detail="Could not determine next run time from provided schedule")
    task.scheduled_for = next_run.isoformat()
    with _scheduled_lock:
        _scheduled_tasks[task_id] = task
        _persist_scheduled_tasks()
    _schedule_timer_for_task(task)
    with _scheduled_lock:
        return _scheduled_tasks[task_id]

@app.patch("/api/scheduled-tasks/{task_id}", response_model=ScheduledTask)
async def update_scheduled_task(task_id: str, req: UpdateTaskRequest):
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    with _scheduled_lock:
        existing = _scheduled_tasks.get(task_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = existing.model_dump()
    task = ScheduledTask(**task_data)
    reschedule_needed = False
    cancel_task = False

    if req.name is not None:
        task.name = req.name.strip() if req.name else None
    if req.query is not None:
        task.query = req.query.strip() if req.query else None

    # Handle interval-based repeat fields
    if req.repeat_interval_seconds is not None:
        if req.repeat_interval_seconds < 0:
            raise HTTPException(status_code=400, detail="repeat_interval_seconds must be non-negative")
        if req.repeat_interval_seconds == 0:
            # Setting to 0 means disable interval-based repeat
            task.repeat_interval_seconds = None
            if task.repeat == "interval":
                task.repeat = None
        else:
            task.repeat_interval_seconds = req.repeat_interval_seconds
            # Set repeat to "interval" if interval is provided
            if not task.repeat or task.repeat not in {"interval", "daily", "weekly"}:
                task.repeat = "interval"
        reschedule_needed = True
    
    if req.repeat_end_time is not None:
        repeat_end_time = (req.repeat_end_time or '').strip() if req.repeat_end_time else None
        if repeat_end_time:
            if not _parse_time_of_day_components(repeat_end_time):
                raise HTTPException(status_code=400, detail="repeat_end_time must be in HH:MM format")
            task.repeat_end_time = repeat_end_time
        else:
            task.repeat_end_time = None
        reschedule_needed = True

    if req.repeat is not None:
        repeat_value = (req.repeat or '').strip().lower()
        if repeat_value and repeat_value not in {"daily", "weekly", "interval"}:
            raise HTTPException(status_code=400, detail="Repeat must be 'daily', 'weekly', or 'interval'")
        task.repeat = repeat_value or None
        if task.repeat and task.repeat != "interval":
            task.delay_seconds = None
            task.repeat_interval_seconds = None
            task.repeat_end_time = None
        elif not task.repeat:
            task.days_of_week = None
            task.repeat_interval_seconds = None
            task.repeat_end_time = None
        reschedule_needed = True

    if req.days_of_week is not None:
        if req.days_of_week:
            try:
                cleaned = sorted({int(d) % 7 for d in req.days_of_week})
            except Exception:
                raise HTTPException(status_code=400, detail="days_of_week must contain integers")
            if any(d < 0 or d > 6 for d in cleaned):
                raise HTTPException(status_code=400, detail="days_of_week entries must be between 0 and 6")
            task.days_of_week = cleaned
        else:
            task.days_of_week = None
        reschedule_needed = True

    if req.delay_seconds is not None or (req.run_at is not None):
        if task.repeat and task.repeat != "interval" and req.delay_seconds is not None:
            raise HTTPException(status_code=400, detail="Repeat schedules cannot use delay_seconds (except interval-based)")
        if req.delay_seconds is not None:
            task.delay_seconds = req.delay_seconds
        if req.run_at is not None:
            task.run_at = req.run_at.strip() if req.run_at else None
        reschedule_needed = True

    if req.status == "cancelled":
        cancel_task = True
        task.status = "cancelled"
        task.scheduled_for = None
    elif reschedule_needed:
        task.status = "scheduled"

    if task.repeat == "weekly" and (not task.days_of_week or len(task.days_of_week) == 0):
        raise HTTPException(status_code=400, detail="Weekly repeat requires days_of_week")
    if task.repeat and task.repeat != "interval" and not (task.run_at and task.run_at.strip()):
        raise HTTPException(status_code=400, detail="Repeat schedules require run_at (except interval-based)")
    if task.repeat == "interval" and not task.repeat_interval_seconds:
        raise HTTPException(status_code=400, detail="Interval-based repeats require repeat_interval_seconds")

    if not cancel_task and reschedule_needed:
        next_run = _compute_next_run_datetime(task)
        if not next_run:
            raise HTTPException(status_code=400, detail="Could not determine next run time from provided schedule")
        task.scheduled_for = next_run.isoformat()
    elif not cancel_task and task.scheduled_for:
        parsed = _normalize_iso_datetime(task.scheduled_for)
        if parsed:
            task.scheduled_for = parsed.isoformat()

    timer_to_cancel = None
    with _scheduled_lock:
        _scheduled_tasks[task_id] = task
        _persist_scheduled_tasks()
        if cancel_task:
            timer_to_cancel = _scheduled_timers.pop(task_id, None)
    if timer_to_cancel:
        try:
            timer_to_cancel.cancel()
        except Exception:
            pass

    if not cancel_task and task.status == "scheduled":
        _schedule_timer_for_task(task)

    with _scheduled_lock:
        return _scheduled_tasks[task_id]

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
        created = datetime.now().replace(microsecond=0)
        new_task = ScheduledTask(
            id=str(uuid.uuid4()),
            name=original.name,
            query=original.query,
            delay_seconds=original.delay_seconds if not original.repeat else None,
            run_at=original.run_at,
            status="scheduled",
            created_at=created.isoformat(),
            scheduled_for=None,
            repeat=original.repeat,
            days_of_week=original.days_of_week,
            last_run_at=None,
            last_run_status=None
        )
        next_run = _compute_next_run_datetime(new_task)
        if not next_run:
            raise HTTPException(status_code=400, detail="Could not determine next run time for repeat task")
        new_task.scheduled_for = next_run.isoformat()
        _scheduled_tasks[new_task.id] = new_task
        _persist_scheduled_tasks()
    _schedule_timer_for_task(new_task)
    with _scheduled_lock:
        return _scheduled_tasks[new_task.id]

# Activity Tracking API Endpoints
class ActivityQueryRequest(BaseModel):
    query: str
    date: Optional[str] = None  # YYYY-MM-DD format
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@app.get("/api/tracking/activity")
async def get_activity(date: Optional[str] = None):
    """Get activity data for a specific date (default: today)."""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if not hasattr(agent, 'activity_tracker') or not agent.activity_tracker:
            raise HTTPException(status_code=503, detail="Activity tracking not available")
        
        storage = agent.activity_tracker.storage
        activities = storage.get_activities(date)
        return activities
    except Exception as e:
        logger.error(f"Error getting activity data: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting activity data: {str(e)}")

@app.get("/api/tracking/activity/range")
async def get_activity_range(start_date: str, end_date: str):
    """Get activities for a date range."""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if not hasattr(agent, 'activity_tracker') or not agent.activity_tracker:
            raise HTTPException(status_code=503, detail="Activity tracking not available")
        
        storage = agent.activity_tracker.storage
        activities = storage.get_activities_range(start_date, end_date)
        return activities
    except Exception as e:
        logger.error(f"Error getting activity range: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting activity range: {str(e)}")

@app.get("/api/tracking/summary")
async def get_summary(date: Optional[str] = None):
    """Get daily summary for a specific date (default: today)."""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if not hasattr(agent, 'activity_tracker') or not agent.activity_tracker:
            raise HTTPException(status_code=503, detail="Activity tracking not available")
        
        storage = agent.activity_tracker.storage
        
        # Get summary if exists
        summary = storage.get_daily_summary(date)
        if summary:
            return summary
        
        # Generate summary if doesn't exist
        if not hasattr(agent, 'activity_analyzer') or not agent.activity_analyzer:
            return {"error": "Activity analyzer not available"}
        
        # Get activities for the date
        activities = storage.get_activities(date)
        screenshots = storage.get_screenshot_metadata(date)
        
        # Calculate summary
        summary = agent.activity_analyzer.calculate_daily_summary(activities, screenshots)
        storage.save_daily_summary(summary)
        
        return summary
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")

@app.get("/api/tracking/summary/range")
async def get_summary_range(start_date: str, end_date: str):
    """Get summaries for a date range."""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if not hasattr(agent, 'activity_tracker') or not agent.activity_tracker:
            raise HTTPException(status_code=503, detail="Activity tracking not available")
        
        storage = agent.activity_tracker.storage
        summaries = storage.get_summaries_range(start_date, end_date)
        return summaries
    except Exception as e:
        logger.error(f"Error getting summary range: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting summary range: {str(e)}")

@app.get("/api/tracking/current")
async def get_current_activity():
    """Get current activity information."""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if not hasattr(agent, 'activity_tracker') or not agent.activity_tracker:
            raise HTTPException(status_code=503, detail="Activity tracking not available")
        
        current = agent.activity_tracker.get_current_activity()
        return current or {"message": "No current activity"}
    except Exception as e:
        logger.error(f"Error getting current activity: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting current activity: {str(e)}")

@app.post("/api/tracking/query")
async def query_activity(request: ActivityQueryRequest):
    """Query activity data using natural language."""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if not hasattr(agent, 'activity_tracker') or not agent.activity_tracker:
            raise HTTPException(status_code=503, detail="Activity tracking not available")
        
        storage = agent.activity_tracker.storage
        
        # Parse query to determine what data to fetch
        query_lower = request.query.lower()
        
        # Determine date range
        if request.date:
            date = request.date
            start_date = date
            end_date = date
        elif request.start_date and request.end_date:
            start_date = request.start_date
            end_date = request.end_date
        elif "today" in query_lower:
            today = datetime.now().strftime("%Y-%m-%d")
            start_date = today
            end_date = today
        elif "yesterday" in query_lower:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            start_date = yesterday
            end_date = yesterday
        elif "week" in query_lower:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        else:
            # Default to today
            today = datetime.now().strftime("%Y-%m-%d")
            start_date = today
            end_date = today
        
        # Get data
        if start_date == end_date:
            activities = storage.get_activities(start_date)
            summary = storage.get_daily_summary(start_date)
            
            # Generate summary if doesn't exist
            if not summary and hasattr(agent, 'activity_analyzer') and agent.activity_analyzer:
                screenshots = storage.get_screenshot_metadata(start_date)
                summary = agent.activity_analyzer.calculate_daily_summary(activities, screenshots)
                storage.save_daily_summary(summary)
        else:
            activities_list = storage.get_activities_range(start_date, end_date)
            summaries = storage.get_summaries_range(start_date, end_date)
            
            # Aggregate data
            activities = {
                "date_range": f"{start_date} to {end_date}",
                "activities": activities_list,
                "summaries": summaries
            }
            summary = None
        
        # Use LLM to generate response
        if hasattr(agent, 'llm') and agent.llm:
            prompt = f"""The user asked: "{request.query}"

Activity data for {start_date}:
{json.dumps(activities, indent=2) if isinstance(activities, dict) else 'Activities retrieved'}

Summary data:
{json.dumps(summary, indent=2) if summary else 'No summary available'}

Provide a natural, conversational response answering the user's question about their activity and productivity. 
Be specific with numbers and insights. If the user asks about focus or productivity, calculate and explain the metrics clearly."""
            
            try:
                from langchain_core.messages import HumanMessage
                response = agent.llm.invoke([HumanMessage(content=prompt)])
                answer = response.content if hasattr(response, 'content') else str(response)
                return {
                    "query": request.query,
                    "response": answer,
                    "data": {
                        "activities": activities,
                        "summary": summary
                    }
                }
            except Exception as e:
                logger.error(f"Error generating LLM response: {e}")
                return {
                    "query": request.query,
                    "response": "I have your activity data, but couldn't generate a response. Here's the raw data.",
                    "data": {
                        "activities": activities,
                        "summary": summary
                    }
                }
        else:
            return {
                "query": request.query,
                "response": "Activity tracking data retrieved. LLM not available for natural language response.",
                "data": {
                    "activities": activities,
                    "summary": summary
                }
            }
    
    except Exception as e:
        logger.error(f"Error querying activity: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying activity: {str(e)}")

@app.get("/api/tracking/timeline")
async def get_timeline(date: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None):
    """
    Get activity timeline with screenshot analysis for a specific date and optional time range.
    
    Args:
        date: Date in YYYY-MM-DD format (default: today)
        start_time: Start time in HH:MM format (e.g., "16:00" for 4pm)
        end_time: End time in HH:MM format (e.g., "18:00" for 6pm)
    
    Returns:
        Combined timeline of activities and screenshot analyses for the specified time period
    """
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if not hasattr(agent, 'activity_tracker') or not agent.activity_tracker:
            raise HTTPException(status_code=503, detail="Activity tracking not available")
        
        storage = agent.activity_tracker.storage
        
        # Default to today if no date provided
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Get activities for the date
        activities_data = storage.get_activities(date)
        app_activities = activities_data.get("app_activities", [])
        
        # Get screenshot metadata for the date
        screenshots = storage.get_screenshot_metadata(date)
        
        # Parse time range if provided
        start_datetime = None
        end_datetime = None
        if start_time:
            try:
                start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid start_time format. Use HH:MM (e.g., '16:00')")
        
        if end_time:
            try:
                end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid end_time format. Use HH:MM (e.g., '18:00')")
        
        # Filter activities by time range
        filtered_activities = []
        for activity in app_activities:
            activity_start = datetime.fromisoformat(activity.get("start_time", ""))
            
            # Check if activity falls within time range
            if start_datetime and activity_start < start_datetime:
                continue
            if end_datetime and activity_start > end_datetime:
                continue
            
            filtered_activities.append(activity)
        
        # Filter screenshots by time range
        filtered_screenshots = []
        for screenshot in screenshots:
            screenshot_time = datetime.fromisoformat(screenshot.get("timestamp", ""))
            
            # Check if screenshot falls within time range
            if start_datetime and screenshot_time < start_datetime:
                continue
            if end_datetime and screenshot_time > end_datetime:
                continue
            
            filtered_screenshots.append(screenshot)
        
        # Combine and sort by timestamp
        timeline = []
        
        # Add activities
        for activity in filtered_activities:
            timeline.append({
                "type": "activity",
                "timestamp": activity.get("start_time"),
                "app_name": activity.get("app_name"),
                "window_title": activity.get("window_title"),
                "duration_seconds": activity.get("duration_seconds", 0),
                "data": activity
            })
        
        # Add screenshots with analysis
        for screenshot in filtered_screenshots:
            timeline.append({
                "type": "screenshot",
                "timestamp": screenshot.get("timestamp"),
                "app_name": screenshot.get("app_name"),
                "window_title": screenshot.get("window_title"),
                "ai_analysis": screenshot.get("ai_analysis", ""),
                "activity_category": screenshot.get("activity_category", "unknown"),
                "focus_score": screenshot.get("focus_score", 50),
                "description": screenshot.get("description", ""),
                "filename": screenshot.get("filename"),
                "data": screenshot
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.get("timestamp", ""))
        
        return {
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "activities": filtered_activities,
            "screenshots": filtered_screenshots,
            "timeline": timeline,
            "count": {
                "activities": len(filtered_activities),
                "screenshots": len(filtered_screenshots),
                "total": len(timeline)
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting timeline: {str(e)}")

@app.get("/api/tracking/stats")
async def get_stats(days: int = 7):
    """Get statistics for the last N days."""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if not hasattr(agent, 'activity_tracker') or not agent.activity_tracker:
            raise HTTPException(status_code=503, detail="Activity tracking not available")
        
        storage = agent.activity_tracker.storage
        
        # Calculate date range
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Get summaries
        summaries = storage.get_summaries_range(start_date, end_date)
        
        # Aggregate statistics
        total_focus_time = sum(s.get("total_focus_time", 0) for s in summaries)
        total_work_time = sum(s.get("work_time", 0) for s in summaries)
        total_research_time = sum(s.get("research_time", 0) for s in summaries)
        total_entertainment_time = sum(s.get("entertainment_time", 0) for s in summaries)
        
        avg_focus_score = 0
        if summaries:
            focus_scores = [s.get("focus_score", 0) for s in summaries if s.get("focus_score")]
            if focus_scores:
                avg_focus_score = sum(focus_scores) / len(focus_scores)
        
        return {
            "period": f"{start_date} to {end_date}",
            "days": len(summaries),
            "total_focus_time": total_focus_time,
            "total_work_time": total_work_time,
            "total_research_time": total_research_time,
            "total_entertainment_time": total_entertainment_time,
            "average_focus_score": round(avg_focus_score, 2),
            "summaries": summaries
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/api/notifications")
async def get_notifications(clear: bool = False):
    """Get pending notifications from activity tracking."""
    global _notification_queue
    
    with _notification_lock:
        notifications = list(_notification_queue)
        if clear:
            _notification_queue.clear()
    
    return {
        "notifications": notifications,
        "count": len(notifications)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
