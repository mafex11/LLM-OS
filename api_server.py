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

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from windows_use.agent.service import Agent
from windows_use.agent.streaming_service import StreamingAgent
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from main import get_running_programs

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

# Global agent instances
agent: Optional[Agent] = None
streaming_agent: Optional[StreamingAgent] = None
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
    """Initialize the agent on server startup"""
    global agent, streaming_agent, agent_initialized
    
    try:
        print("Initializing Windows-Use Agent...")
        
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
        
        # Initialize regular agent
        agent = Agent(
            llm=llm,
            browser='chrome',
            use_vision=False,
            enable_conversation=True,
            literal_mode=True,
            max_steps=30,
            enable_tts=True,
            tts_voice_id="21m00Tcm4TlvDq8ikWAM"
        )
        
        # Initialize streaming agent
        streaming_agent = StreamingAgent(
            llm=llm,
            browser='chrome',
            use_vision=False,
            enable_conversation=True,
            literal_mode=True,
            max_steps=30,
            enable_tts=True,
            tts_voice_id="21m00Tcm4TlvDq8ikWAM"
        )
        
        # Get running programs
        running_programs = get_running_programs()
        agent.running_programs = running_programs
        streaming_agent.running_programs = running_programs
        
        # Pre-warm the system
        agent.desktop.get_state(use_vision=False)
        streaming_agent.desktop.get_state(use_vision=False)
        
        agent_initialized = True
        print("Agent and StreamingAgent initialized successfully!")
        
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        agent_initialized = False

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
        # Process the query
        response = agent.invoke(request.query)
        
        # Extract response content
        if hasattr(response, 'content') and response.content:
            response_text = response.content
        else:
            response_text = str(response)
        
        return QueryResponse(
            response=response_text,
            success=True,
            timestamp=datetime.now(),
            error=None
        )
        
    except Exception as e:
        return QueryResponse(
            response="",
            success=False,
            timestamp=datetime.now(),
            error=str(e)
        )

# Streaming query endpoint for real-time responses
@app.post("/api/query/stream")
async def process_query_stream(request: QueryRequest):
    """Process a query with streaming response"""
    if not agent_initialized or not streaming_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    async def generate_response():
        try:
            # Process the query with streaming
            async for update in streaming_agent.invoke_streaming(request.query):
                # Send update as Server-Sent Event
                yield f"data: {json.dumps(update)}\n\n"
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.1)
            
        except Exception as e:
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
