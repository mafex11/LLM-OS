import logging
import re
from typing import Optional, Dict, Any
from overlay_ui import update_overlay_status

class OverlayLogger:
    """
    Custom logger that captures agent execution information and sends it to the overlay UI.
    """
    
    def __init__(self):
        self.current_iteration = 0
        self.current_max_steps = 30
        self.current_phase = "Ready"
        self.current_action = ""
        self.current_details = ""
        
    def log_agent_info(self, message: str):
        """Process agent log messages and extract status information"""
        try:
            # Extract iteration number
            iteration_match = re.search(r'Iteration: (\d+)', message)
            if iteration_match:
                self.current_iteration = int(iteration_match.group(1))
                update_overlay_status(
                    iteration=self.current_iteration,
                    max_steps=self.current_max_steps
                )
            
            # Extract evaluate information
            evaluate_match = re.search(r'Evaluate: (.+)', message)
            if evaluate_match:
                evaluate_text = evaluate_match.group(1).strip()
                update_overlay_status(evaluate=evaluate_text)
            
            # Extract memory information
            memory_match = re.search(r'Memory: (.+)', message)
            if memory_match:
                memory_text = memory_match.group(1).strip()
                update_overlay_status(memory=memory_text)
            
            # Extract plan information
            plan_match = re.search(r'Plan: (.+)', message)
            if plan_match:
                plan_text = plan_match.group(1).strip()
                update_overlay_status(plan=plan_text)
            
            # Extract thought information
            thought_match = re.search(r'Thought: (.+)', message)
            if thought_match:
                thought_text = thought_match.group(1).strip()
                update_overlay_status(thought=thought_text)
            
            # Extract action information
            action_match = re.search(r'Action: (.+)', message)
            if action_match:
                action_text = action_match.group(1).strip()
                self.current_action = action_text
                update_overlay_status(action=action_text)
            
            # Extract observation information
            observation_match = re.search(r'Observation: (.+)', message)
            if observation_match:
                observation_text = observation_match.group(1).strip()
                # Truncate long observations
                if len(observation_text) > 200:
                    observation_text = observation_text[:200] + "..."
                update_overlay_status(tool_result=observation_text)
                
        except Exception as e:
            print(f"Error processing overlay log: {e}")
    
    def update_phase(self, phase: str, action: str = "", details: str = ""):
        """Update the current phase and action"""
        self.current_phase = phase
        self.current_action = action
        self.current_details = details
        
        update_overlay_status(
            phase=phase,
            action=action,
            details=details
        )
    
    def update_iteration(self, iteration: int, max_steps: int = 30):
        """Update iteration information"""
        self.current_iteration = iteration
        self.current_max_steps = max_steps
        
        update_overlay_status(
            iteration=iteration,
            max_steps=max_steps
        )

# Global overlay logger instance
overlay_logger = OverlayLogger()

class OverlayHandler(logging.Handler):
    """
    Custom logging handler that sends log messages to the overlay UI.
    """
    
    def emit(self, record):
        """Emit a log record to the overlay"""
        try:
            message = self.format(record)
            overlay_logger.log_agent_info(message)
        except Exception:
            pass  # Ignore errors to prevent infinite loops

def setup_overlay_logging():
    """Setup logging to send agent information to overlay"""
    # Create overlay handler
    overlay_handler = OverlayHandler()
    overlay_handler.setLevel(logging.INFO)
    
    # Add handler to agent logger
    agent_logger = logging.getLogger('windows_use.agent.service')
    agent_logger.addHandler(overlay_handler)
    
    # Also add to root logger to catch all agent-related logs
    root_logger = logging.getLogger()
    root_logger.addHandler(overlay_handler)
    
    return overlay_handler

def remove_overlay_logging(handler):
    """Remove overlay logging handler"""
    try:
        agent_logger = logging.getLogger('windows_use.agent.service')
        agent_logger.removeHandler(handler)
        
        root_logger = logging.getLogger()
        root_logger.removeHandler(handler)
    except Exception:
        pass



