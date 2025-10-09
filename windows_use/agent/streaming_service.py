"""
Streaming service for real-time agent thinking and tool usage updates
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
from windows_use.agent.service import Agent
from windows_use.agent.state import AgentState
from windows_use.desktop.service import Desktop
from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)

class StreamingAgent(Agent):
    """
    Enhanced Agent that can stream real-time thinking and tool usage updates
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.streaming_callbacks = []
    
    def add_streaming_callback(self, callback):
        """Add a callback function to receive streaming updates"""
        self.streaming_callbacks.append(callback)
    
    async def emit_update(self, update_type: str, data: Dict[str, Any]):
        """Emit a streaming update to all registered callbacks"""
        update = {
            "type": update_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        for callback in self.streaming_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                logger.error(f"Error in streaming callback: {e}")
    
    def show_status(self, status: str, action_name: str = None, details: str = None):
        """Enhanced status display that also streams updates"""
        # Call parent method for console output
        super().show_status(status, action_name, details)
        
        # Emit streaming update
        asyncio.create_task(self.emit_update("status", {
            "status": status,
            "action_name": action_name,
            "details": details
        }))
    
    async def invoke_streaming(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a query with streaming updates - uses the parent invoke() method
        """
        try:
            # Send initial thinking update
            start_update = {
                "type": "thinking",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "message": "Processing your request...",
                    "step": "initialization"
                }
            }
            yield start_update
            
            # Use the parent's invoke method in a thread pool executor
            # This is the same method used by main.py CLI - it works!
            loop = asyncio.get_running_loop()
            
            # Run the synchronous invoke in a thread
            result = await loop.run_in_executor(None, self.invoke, query)
            
            # Extract the response content
            if hasattr(result, 'content'):
                final_output = result.content
            else:
                final_output = str(result)
            # Send the final response
            response_update = {
                "type": "response",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "message": final_output if final_output else "Task completed.",
                    "success": True
                }
            }
            yield response_update
                
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error in streaming invoke: {e}\n{error_traceback}")
            
            error_update = {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "message": str(e),
                    "error_type": type(e).__name__
                }
            }
            await self.emit_update("error", error_update["data"])
            yield error_update
        
        # Emit and yield completion
        complete_update = {
            "type": "complete",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "message": "Processing complete"
            }
        }
        await self.emit_update("complete", complete_update["data"])
        yield complete_update
