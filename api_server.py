"""
FastAPI Server for Windows-Use Agent
Provides REST API endpoints for the Next.js frontend
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from windows_use.agent.service import Agent
from windows_use.agent.logger import agent_logger
from windows_use.agent.streaming_wrapper import StreamingAgentWrapper
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from main import get_running_programs
import threading

# Initialize FastAPI app
app = FastAPI(
    title="Windows-Use Agent API",
    description="REST API for Windows automation agent",
    version="1.0.0"
)

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent: Optional[Agent] = None
streaming_wrapper: Optional[StreamingAgentWrapper] = None
agent_initialized = False

# Request/Response Models
class QueryRequest(BaseModel):
    query: str
    use_vision: bool = False

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
    max_steps: int = 30

# Initialize agent on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the agent on server startup - SAME AS main.py"""
    global agent, streaming_wrapper, agent_initialized
    
    try:
        print("Initializing Windows-Use Agent...")
        
        # Log session start (matching CLI behavior)
        agent_logger.log_session_start()
        
        # Initialize LLM with API key
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it in your .env file.")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            temperature=0.3,
            google_api_key=google_api_key
        )
        
        # TTS configuration (matching CLI behavior)
        enable_tts = os.getenv("ENABLE_TTS", "true").lower() == "true"
        tts_voice_id = os.getenv("TTS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        
        # Initialize agent (SAME PARAMS AS main.py line 364!)
        agent = Agent(
            llm=llm,
            browser='chrome',
            use_vision=False,
            enable_conversation=True,
            literal_mode=True,
            max_steps=30,
            enable_tts=enable_tts,
            tts_voice_id=tts_voice_id
        )
        
        # Get running programs (SAME AS main.py line 354!)
        running_programs = get_running_programs()
        agent.running_programs = running_programs
        
        # Pre-warm the system (SAME AS main.py line 383!)
        print("Pre-warming system for faster response...")
        try:
            agent.desktop.get_state(use_vision=False)
            print("System pre-warmed successfully!")
        except Exception as e:
            print(f"Pre-warming failed: {e}")
            print("System will still work, but first response may be slower.")
        
        # Show TTS status (matching CLI behavior)
        if enable_tts:
            from windows_use.agent.tts_service import is_tts_available
            tts_available = is_tts_available()
            print(f"TTS Status: {'Enabled' if tts_available else 'Disabled (API key not configured)'}")
        else:
            print("TTS Status: Disabled")
        
        # Create streaming wrapper to capture status updates
        streaming_wrapper = StreamingAgentWrapper(agent)
        
        agent_initialized = True
        print("Agent initialized successfully!")
        
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        agent_initialized = False

# Shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    """Handle server shutdown"""
    try:
        # Log session end (matching CLI behavior)
        agent_logger.log_session_end()
        print("Session logged successfully on shutdown.")
    except Exception as e:
        print(f"Error logging session end: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_ready": agent_initialized,
        "timestamp": datetime.now().isoformat()
    }

# System status endpoint
@app.get("/api/status", response_model=SystemStatus)
async def get_system_status():
    """Get current system status"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Get running programs
        running_programs = get_running_programs()
        apps = [
            AppInfo(name=prog['name'], title=prog['title'], id=str(prog['id']))
            for prog in running_programs
        ]
        
        # Get memory stats
        memory_stats = {}
        if hasattr(agent, 'get_memory_stats'):
            memory_stats = agent.get_memory_stats()
        
        # Get performance stats
        performance_stats = {}
        if hasattr(agent, 'performance_monitor'):
            performance_stats = agent.performance_monitor.get_stats()
        
        return SystemStatus(
            agent_ready=True,
            running_programs=apps,
            memory_stats=memory_stats,
            performance_stats=performance_stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")

# Query endpoint
@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """Process a query through the agent"""
    if not agent_initialized or not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Process the query (matching CLI behavior)
        print(f"Processing query: {request.query}")
        response = agent.invoke(request.query)
        
        # Extract response content (matching CLI behavior)
        if hasattr(response, 'content') and response.content:
            response_text = response.content
        else:
            response_text = str(response)
        
        print(f"Response: {response_text[:100]}...")  # Log first 100 chars
        
        return QueryResponse(
            response=response_text,
            success=True,
            timestamp=datetime.now(),
            error=None
        )
        
    except Exception as e:
        print(f"Query processing error: {e}")
        return QueryResponse(
            response="",
            success=False,
            timestamp=datetime.now(),
            error=str(e)
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
            
            # Container for the result
            result_container = {"response": None, "error": None, "done": False}
            
            def run_agent():
                """Run agent in background thread"""
                try:
                    result_container["response"] = streaming_wrapper.invoke(request.query)
                    result_container["done"] = True
                except Exception as e:
                    result_container["error"] = e
                    result_container["done"] = True
            
            # Start agent in background thread
            thread = threading.Thread(target=run_agent)
            thread.start()
            
            # Stream status updates while agent is running
            last_status = None
            while not result_container["done"]:
                # Get new status updates
                updates = streaming_wrapper.get_status_updates()
                
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
            
            # Extract and send final response
            response = result_container["response"]
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
            
        except Exception as e:
            import traceback
            print(f"Streaming error: {e}\n{traceback.format_exc()}")
            error_update = {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "message": str(e),
                    "error_type": type(e).__name__
                }
            }
            yield f"data: {json.dumps(error_update)}\n\n"
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
