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
        Process a query with streaming updates
        """
        try:
            # Emit start thinking
            await self.emit_update("thinking", {
                "message": "Starting to process your request...",
                "step": "initialization"
            })
            
            # Create initial state
            state = AgentState({
                'input': query,
                'steps': 0,
                'max_steps': self.max_steps,
                'messages': [],
                'previous_observation': None,
                'agent_data': None,
                'output': None
            })
            
            # Process through the agent workflow
            current_state = state
            step_count = 0
            
            while step_count < self.max_steps:
                step_count += 1
                current_state['steps'] = step_count
                
                # Emit reasoning step
                await self.emit_update("thinking", {
                    "message": f"Planning step {step_count}...",
                    "step": "reasoning"
                })
                
                # Reason about next action
                current_state = self.reason(current_state)
                
                if current_state.get('agent_data') is None:
                    # No more actions needed
                    break
                
                # Emit tool usage
                agent_data = current_state['agent_data']
                tool_name = agent_data.action.name
                tool_params = agent_data.action.params
                
                await self.emit_update("tool_usage", {
                    "tool_name": tool_name,
                    "tool_params": tool_params,
                    "step": step_count
                })
                
                # Execute the tool
                await self.emit_update("thinking", {
                    "message": f"Executing {tool_name}...",
                    "step": "execution"
                })
                
                current_state = self.answer(current_state)
                
                # Check if we're done
                if current_state.get('output'):
                    break
            
            # Emit final response
            final_output = current_state.get('output', '')
            if final_output:
                await self.emit_update("response", {
                    "content": final_output,
                    "success": True
                })
            else:
                await self.emit_update("response", {
                    "content": "I've completed the requested task.",
                    "success": True
                })
                
        except Exception as e:
            logger.error(f"Error in streaming invoke: {e}")
            await self.emit_update("error", {
                "message": str(e),
                "error_type": type(e).__name__
            })
        
        # Emit completion
        await self.emit_update("complete", {
            "message": "Processing complete"
        })
