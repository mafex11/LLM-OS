"""
Comprehensive logging system for Yuki AI Agent
Logs all actions, thoughts, observations to app.log
"""
import logging
from datetime import datetime
from pathlib import Path

class AgentLogger:
    def __init__(self, log_file: str = "app.log"):
        self.log_file = log_file
        self.setup_logger()
    
    def setup_logger(self):
        """Setup file logger with append mode"""
        # Create logger
        self.logger = logging.getLogger('windows_use')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # Create file handler that appends
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create detailed formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
    
    def log_session_start(self):
        """Log session start"""
        self.logger.info("=" * 80)
        self.logger.info("NEW SESSION STARTED")
        self.logger.info("=" * 80)
    
    def log_session_end(self):
        """Log session end"""
        self.logger.info("=" * 80)
        self.logger.info("SESSION ENDED")
        self.logger.info("=" * 80 + "\n")
    
    def log_user_query(self, query: str):
        """Log user query"""
        self.logger.info(f"USER QUERY: {query}")
    
    def log_iteration(self, iteration: int, max_steps: int):
        """Log iteration number"""
        self.logger.info(f"--- ITERATION {iteration}/{max_steps} ---")
    
    def log_evaluate(self, evaluate: str):
        """Log evaluation"""
        self.logger.info(f"EVALUATE: {evaluate}")
    
    def log_plan(self, plan: str):
        """Log plan"""
        self.logger.info(f"PLAN: {plan}")
    
    def log_thought(self, thought: str):
        """Log thought process"""
        self.logger.info(f"THOUGHT: {thought}")
    
    def log_action(self, action_name: str, params: dict):
        """Log action execution"""
        params_str = ', '.join(f'{k}={v}' for k, v in params.items())
        self.logger.info(f"ACTION: {action_name}({params_str})")
    
    def log_observation(self, observation: str):
        """Log observation/result"""
        self.logger.info(f"OBSERVATION: {observation}")
    
    def log_final_answer(self, answer: str):
        """Log final answer"""
        self.logger.info(f"FINAL ANSWER: {answer}")
    
    def log_error(self, error: str):
        """Log error"""
        self.logger.error(f"ERROR: {error}")
    
    def log_desktop_state(self, state_info: str):
        """Log desktop state information"""
        self.logger.debug(f"DESKTOP STATE: {state_info}")
    
    def log_tool_result(self, tool_name: str, success: bool, result: str):
        """Log tool execution result"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"TOOL RESULT [{status}] {tool_name}: {result}")
    
    def log_conversation_cleared(self):
        """Log conversation history clear"""
        self.logger.info("CONVERSATION HISTORY CLEARED")
    
    def log_tts(self, text: str):
        """Log TTS output"""
        self.logger.debug(f"TTS: {text}")
    
    def log_stt(self, text: str):
        """Log STT input"""
        self.logger.debug(f"STT: {text}")
    
    def log_info(self, message: str):
        """Log general info"""
        self.logger.info(message)
    
    def log_debug(self, message: str):
        """Log debug info"""
        self.logger.debug(message)

# Global logger instance
agent_logger = AgentLogger()

