"""
Streaming wrapper that captures agent status updates in real-time
"""
import asyncio
import queue
from typing import Optional
from windows_use.agent.service import Agent

class StreamingAgentWrapper:
    """Wraps an Agent to capture and stream status updates"""
    
    def __init__(self, agent: Agent):
        self.agent = agent
        self.status_queue = queue.Queue()
        self.original_show_status = agent.show_status
        
        # Override the agent's show_status method
        self.agent.show_status = self._capture_status
    
    def _capture_status(self, status: str, action_name: str = None, details: str = None):
        """Capture status updates and put them in queue"""
        # Call original method to maintain console output
        self.original_show_status(status, action_name, details)
        
        # Put update in queue for streaming
        update = {
            "status": status,
            "action_name": action_name,
            "details": details
        }
        self.status_queue.put(update)
    
    def get_status_updates(self):
        """Get all queued status updates"""
        updates = []
        while not self.status_queue.empty():
            try:
                updates.append(self.status_queue.get_nowait())
            except queue.Empty:
                break
        return updates
    
    def invoke(self, query: str):
        """Invoke the agent and return response"""
        # Clear any old updates
        while not self.status_queue.empty():
            try:
                self.status_queue.get_nowait()
            except queue.Empty:
                break
        
        # Invoke the agent
        return self.agent.invoke(query)

