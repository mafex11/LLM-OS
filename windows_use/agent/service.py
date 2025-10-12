from windows_use.agent.tools.service import click_tool, type_tool, launch_tool, shell_tool, clipboard_tool, done_tool, shortcut_tool, scroll_tool, drag_tool, move_tool, key_tool, wait_tool, scrape_tool, switch_tool, resize_tool, human_tool, system_tool
from windows_use.agent.tts_service import TTSService, speak_text, is_tts_available
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from windows_use.agent.utils import extract_agent_data, image_message
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from windows_use.agent.registry.views import ToolResult
from windows_use.agent.registry.service import Registry
from windows_use.agent.prompt.service import Prompt
# from windows_use.agent.memory import MemoryManager  # Disabled: agent memory system
from windows_use.agent.performance import PerformanceMonitor, timed
from windows_use.agent.logger import agent_logger
from live_inspect.watch_cursor import WatchCursor
from langgraph.graph import START,END,StateGraph
from windows_use.agent.views import AgentResult
from windows_use.desktop.service import Desktop
from windows_use.agent.state import AgentState
from langchain_core.tools import BaseTool
from rich.markdown import Markdown
from rich.console import Console
from termcolor import colored
from textwrap import shorten
from typing import Literal
import logging
import sys
import time
import ctypes
import threading

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Import overlay functionality
try:
    from overlay_ui import update_overlay_status
    OVERLAY_AVAILABLE = True
except ImportError:
    OVERLAY_AVAILABLE = False
    def update_overlay_status(**kwargs):
        pass

class Agent:
    '''
    Windows Use

    An agent that can interact with GUI elements on Windows

    Args:
        instructions (list[str], optional): Instructions for the agent. Defaults to [].
        browser (Literal['edge', 'chrome', 'firefox'], optional): Browser the agent should use (Make sure this browser is installed). Defaults to 'edge'.
        additional_tools (list[BaseTool], optional): Additional tools for the agent. Defaults to [].
        llm (BaseChatModel): Language model for the agent. Defaults to None.
        consecutive_failures (int, optional): Maximum number of consecutive failures for the agent. Defaults to 3.
        max_steps (int, optional): Maximum number of steps for the agent. Defaults to 100.
        use_vision (bool, optional): Whether to use vision for the agent. Defaults to False.
    
    Returns:
        Agent
    '''
    def __init__(self,instructions:list[str]=[],additional_tools:list[BaseTool]=[],browser:Literal['edge','chrome','firefox']='edge', llm: BaseChatModel=None,consecutive_failures:int=3,max_steps:int=20,use_vision:bool=False,enable_conversation:bool=True,literal_mode:bool=True,enable_tts:bool=False,tts_voice_id:str="21m00Tcm4TlvDq8ikWAM"):
        self.name='Windows Use'
        self.description='An agent that can interact with GUI elements on Windows' 
        self.registry = Registry([
            click_tool,type_tool, launch_tool, shell_tool, clipboard_tool,
            done_tool, shortcut_tool, scroll_tool, drag_tool, move_tool,
            key_tool, wait_tool, scrape_tool, switch_tool, resize_tool, human_tool, system_tool
        ] + additional_tools)
        self.instructions=instructions
        self.browser=browser
        self.max_steps=max_steps
        self.consecutive_failures=consecutive_failures
        self.use_vision=use_vision
        self.enable_conversation=enable_conversation
        self.literal_mode=literal_mode
        self.enable_tts=enable_tts
        self.tts_voice_id=tts_voice_id
        self.llm = llm or ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
        self.watch_cursor = WatchCursor()
        self.desktop = Desktop()
        self.console=Console(file=sys.stderr)  # Use stderr to avoid interfering with stdin
        self.graph=self.create_graph()
        # Conversation history
        self.conversation_history = []
        self.system_message = None
        # Memory management (disabled)
        # self.memory_manager = MemoryManager()
        self.current_task_steps = []  # Track steps for current task
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        # TTS service
        self.tts_service = TTSService(voice_id=tts_voice_id, enable_tts=enable_tts) if enable_tts else None
        # Cooperative pause controller
        self._pause_event = threading.Event()
        self._pause_event.clear()  # not paused by default
        self._pause_lock = threading.Lock()

    def pause(self):
        """Request a cooperative pause. Running steps will wait at checkpoints."""
        with self._pause_lock:
            self._pause_event.set()

    def resume(self):
        """Resume execution after a cooperative pause."""
        with self._pause_lock:
            self._pause_event.clear()

    def is_paused(self) -> bool:
        """Check if the agent is currently paused."""
        return self._pause_event.is_set()

    def _wait_if_paused(self, checkpoint_name: str = ""):
        """Block cooperatively while paused, emitting a status message once."""
        if not self._pause_event.is_set():
            return
        # Announce pause once per checkpoint entry
        self.show_status("Paused", "Stop/Wait", f"Waiting at checkpoint: {checkpoint_name}")
        # Spin-wait cooperatively with small sleeps to reduce CPU
        while self._pause_event.is_set():
            time.sleep(0.05)

    def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []
        self.system_message = None
        agent_logger.log_conversation_cleared()
        
    
    def _should_use_precise_detection(self, query: str, action_name: str = None) -> str:
        """
        Determine if we should use precise detection for a specific application.
        Returns the target app name or None.
        """
        query_lower = query.lower()
        
        # Calculator detection
        if any(keyword in query_lower for keyword in ['calculator', 'calc', 'calculate', 'math', 'add', 'subtract', 'multiply', 'divide']):
            return 'calculator'
        
        # Notepad detection
        if any(keyword in query_lower for keyword in ['notepad', 'text editor', 'write', 'type text']):
            return 'notepad'
        
        # Browser detection
        if any(keyword in query_lower for keyword in ['browser', 'chrome', 'firefox', 'edge', 'website', 'url']):
            return 'browser'
        
        return None

    def _is_chrome_focused(self) -> bool:
        """Check if Chrome is currently focused"""
        try:
            if not hasattr(self.desktop, 'desktop_state') or not self.desktop.desktop_state:
                return False
            
            active_app = self.desktop.desktop_state.active_app
            if not active_app:
                return False
            
            # Check if the active app name contains Chrome-related keywords
            chrome_keywords = ['chrome', 'google chrome', 'browser']
            active_name = active_app.name.lower()
            
            is_chrome = any(keyword in active_name for keyword in chrome_keywords)
            return is_chrome
            
        except Exception as e:
            return False

    def _find_control_type_for_coordinates(self, click_loc: tuple[int, int]) -> str:
        """
        Find the control_type for given coordinates from the current desktop state.
        Returns the control_type or None if not found.
        """
        try:
            if not self.desktop.desktop_state or not self.desktop.desktop_state.tree_state:
                return None
            
            x, y = click_loc
            tree_state = self.desktop.desktop_state.tree_state
            
            # Check interactive elements first
            for element in tree_state.interactive_nodes:
                bbox = element.bounding_box
                if (bbox.left <= x <= bbox.right and bbox.top <= y <= bbox.bottom):
                    return element.control_type
            
            # Check scrollable elements
            for element in tree_state.scrollable_nodes:
                bbox = element.bounding_box
                if (bbox.left <= x <= bbox.right and bbox.top <= y <= bbox.bottom):
                    return element.control_type
            
            return None
        except Exception:
            return None

    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation history"""
        if not self.conversation_history:
            return "No previous conversation."
        
        summary = "Previous conversation:\n"
        for i, message in enumerate(self.conversation_history[-6:], 1):  # Last 6 messages
            if isinstance(message, HumanMessage):
                summary += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                # Extract just the final answer or key info from AI messages
                content = message.content
                if "Final Answer:" in content:
                    answer_part = content.split("Final Answer:")[-1].strip()
                    summary += f"Agent: {answer_part[:100]}...\n"
                else:
                    summary += f"Agent: {content[:100]}...\n"
        return summary

    def check_memory(self, query: str) -> str:
        """Check if we have a memory for this query (disabled)"""
        # solution_steps = self.memory_manager.get_memory_solution(query)
        # if solution_steps:
        #     self.console.print(f"[bold green]Found memory for similar task![/bold green]")
        #     self.console.print(f"[dim]Previous solution had {len(solution_steps)} steps[/dim]")
        #     return f"Found previous solution with {len(solution_steps)} steps. Applying known solution..."
        return ""

    def save_successful_task(self, query: str, steps: list, tags: list = None):
        """Save a successful task solution to memory (disabled)"""
        # if steps:
        #     key = self.memory_manager.add_memory(query, steps, tags)
        #     self.console.print(f"[bold green]Saved solution to memory (ID: {key})[/bold green]")
        return

    def get_memory_stats(self) -> dict:
        """Get memory statistics (disabled)"""
        # return self.memory_manager.get_memory_stats()
        return {}

    def list_memories(self) -> list:
        """List all stored memories (disabled)"""
        # return self.memory_manager.list_memories()
        return []

    def clear_memories(self):
        """Clear all memories (disabled)"""
        # self.memory_manager.clear_memories()
        # self.console.print("[bold yellow]All memories cleared[/bold yellow]")
        return

    def show_status(self, status: str, action_name: str = None, details: str = None):
        """Display real-time status updates"""
        if action_name and details:
            logger.info(colored(f"[{status}] {action_name}: {details}", color='yellow'))
        elif action_name:
            logger.info(colored(f"[{status}] {action_name}", color='yellow'))
        else:
            logger.info(colored(f"[{status}]", color='yellow'))
            

    @timed("reason")
    def reason(self,state:AgentState):
        # Cooperative pause checkpoint before planning
        self._wait_if_paused("reason")
        
        steps=state.get('steps')
        max_steps=state.get('max_steps')
        messages=state.get('messages')
        
        # Show reasoning status
        self.show_status("Thinking", "Planning Next Action", f"Step {steps}/{max_steps}")
        
        # Only refresh desktop state if previous action was Launch Tool and state is stale
        if steps > 1:  # Not the first step
            previous_observation = state.get('previous_observation', '')
            if 'launched and desktop state refreshed' in previous_observation:
                # Check if desktop state is recent enough
                current_time = time.time()
                if (not hasattr(self.desktop, '_last_state_time') or 
                    current_time - getattr(self.desktop, '_last_state_time', 0) > 1.0):
                    self.show_status("Refreshing", "Desktop State", "Getting updated coordinates for planning")
                    # Use precise detection if we're working with a specific app
                    target_app = self._should_use_precise_detection(state.get('input', ''))
                    fresh_desktop_state = self.desktop.get_state(use_vision=self.use_vision, target_app=target_app)
                    self.desktop._last_state_time = current_time
                else:
                    fresh_desktop_state = self.desktop.desktop_state
                # Update the last message with fresh desktop state
                if messages:
                    last_message = messages[-1]
                    if isinstance(last_message, HumanMessage):
                        # Recreate the observation prompt with fresh desktop state
                        fresh_prompt = Prompt.observation_prompt(
                            query=state.get('input'),
                            steps=steps-1,
                            max_steps=max_steps,
                            tool_result=ToolResult(is_success=True, content=previous_observation),
                            desktop_state=fresh_desktop_state
                        )
                        messages[-1] = HumanMessage(content=fresh_prompt)
        
        message=self.llm.invoke(messages)
        agent_data = extract_agent_data(message=message)
        
        # Log to file
        agent_logger.log_iteration(steps, max_steps)
        agent_logger.log_evaluate(agent_data.evaluate)
        agent_logger.log_plan(agent_data.plan)
        agent_logger.log_thought(agent_data.thought)
        
        # Log to console
        logger.info(colored(f"{agent_data.thought}",color='light_magenta'))
        
        # Send thought to streaming clients
        self.show_status("Reasoning", "Agent Thought", agent_data.thought)
        
        # Update overlay with agent data
        if OVERLAY_AVAILABLE:
            update_overlay_status(
                iteration=steps,
                max_steps=state.get('max_steps', 30),
                evaluate=agent_data.evaluate,
                # memory=agent_data.memory,  # disabled
                plan=agent_data.plan,
                thought=agent_data.thought
            )
        last_message = state.get('messages').pop()
        if isinstance(last_message, HumanMessage):
            message=HumanMessage(content=Prompt.previous_observation_prompt(steps=steps,max_steps=max_steps,observation=state.get('previous_observation')))
            return {**state,'agent_data':agent_data,'messages':[message],'steps':steps+1}

    @timed("action")
    def action(self,state:AgentState):
        # Cooperative pause checkpoint before executing an action
        self._wait_if_paused("action:start")
        
        steps=state.get('steps')
        max_steps=state.get('max_steps')
        agent_data=state.get('agent_data')
        name = agent_data.action.name
        params = agent_data.action.params
        ai_message = AIMessage(content=Prompt.action_prompt(agent_data=agent_data))
        
        # Show status update before action
        self.show_status("Executing", name, f"Step {steps}/{max_steps}")
        
        
        # Only refresh desktop state before coordinate-based actions if it's stale
        if name in ['Click Tool', 'Type Tool', 'Scroll Tool', 'Drag Tool', 'Move Tool']:
            # Use precise detection for specific applications
            target_app = self._should_use_precise_detection(str(params))
            
            # Only refresh if we don't have recent desktop state
            current_time = time.time()
            if (not hasattr(self.desktop, '_last_state_time') or 
                current_time - getattr(self.desktop, '_last_state_time', 0) > 1.5):
                self.desktop.get_state(use_vision=self.use_vision, target_app=target_app)
                self.desktop._last_state_time = current_time
                self.show_status("Refreshing", "Desktop State", "Getting updated coordinates")
        
        # OPTIMIZATION: For Click Tool and Type Tool, find control_type from desktop state
        if name in ['Click Tool', 'Type Tool'] and 'loc' in params:
            action_loc = params['loc']
            control_type = self._find_control_type_for_coordinates(action_loc)
            if control_type:
                params['control_type'] = control_type
        
        # Log action to file
        agent_logger.log_action(name, params)
        
        # Show tool usage (skip for Human Tool as it's handled separately)
        if name != 'Human Tool':
            logger.info(colored(f"Using {name}...",color='blue'))
        
        tool_result = self.registry.execute(tool_name=name, desktop=self.desktop, **params)
        observation=tool_result.content if tool_result.is_success else tool_result.error
        
        # Log tool result to file
        agent_logger.log_tool_result(name, tool_result.is_success, observation)
        
        # Update overlay with action result
        if OVERLAY_AVAILABLE:
            update_overlay_status(
                action=name,
                tool_result=observation
            )
        
        # Track step for memory (disabled)
        # if tool_result.is_success and name != 'Done Tool':
        #     step_info = {
        #         'action': name,
        #         'params': params,
        #         'result': observation
        #     }
        #     self.current_task_steps.append(step_info)
        
        # Show completion status
        if tool_result.is_success:
            self.show_status("Completed", name, "Success")
        else:
            self.show_status("Failed", name, f"{observation[:50]}...")
        
        # Force desktop state refresh after Launch Tool to get updated coordinates
        if tool_result.is_success and name == 'Launch Tool':
            self.show_status("Refreshing", "Desktop State", "Getting fresh coordinates after launch")
            self.desktop.get_state(use_vision=self.use_vision)
            self.desktop._last_state_time = time.time()
        
        # Cooperative pause checkpoint after action side-effects settle
        self._wait_if_paused("action:end")
        
        # Log observation to file
        agent_logger.log_observation(observation)
        
        # Show observation (skip for Human Tool as it's a question)
        if name != 'Human Tool':
            logger.info(colored(f"{shorten(observation,500,placeholder='...')}",color='green'))
        # Only get fresh desktop state if we don't have recent state
        current_time = time.time()
        if (not hasattr(self.desktop, '_last_state_time') or 
            current_time - getattr(self.desktop, '_last_state_time', 0) > 1.0):
            desktop_state = self.desktop.get_state(use_vision=self.use_vision)
            self.desktop._last_state_time = current_time
        else:
            desktop_state = self.desktop.desktop_state or self.desktop.get_state(use_vision=self.use_vision)
        prompt=Prompt.observation_prompt(query=state.get('input'),steps=steps,max_steps=max_steps, tool_result=tool_result, desktop_state=desktop_state)
        human_message=image_message(prompt=prompt,image=desktop_state.screenshot) if self.use_vision and desktop_state.screenshot else HumanMessage(content=prompt)
        return {**state,'agent_data':None,'messages':[ai_message, human_message],'previous_observation':observation}

    def _should_use_conversational_processing(self, raw_answer: str, original_query: str) -> bool:
        """
        Determine if conversational processing is needed.
        Skip for simple responses to improve performance.
        """
        # Skip conversational processing for simple responses
        simple_patterns = [
            'hi', 'hello', 'hey', 'how are you', 'what\'s up', 'good morning', 'good evening',
            'thanks', 'thank you', 'bye', 'goodbye', 'see you'
        ]
        
        # Check if query is a simple greeting/courtesy
        query_lower = original_query.lower().strip()
        if any(pattern in query_lower for pattern in simple_patterns):
            return False
        
        # Check if answer is already conversational (contains natural language)
        answer_lower = raw_answer.lower()
        conversational_indicators = ['i\'ve', 'i\'m', 'you\'ve', 'you\'re', 'let me', 'i\'ll', 'i can']
        if any(indicator in answer_lower for indicator in conversational_indicators):
            return False
        
        # Check answer length - short answers don't need processing
        if len(raw_answer) < 100:
            return False
        
        # Check if answer contains technical data that might benefit from conversion
        technical_indicators = ['status code:', 'coordinates:', 'file path:', 'process id:', 'error code:']
        if any(indicator in answer_lower for indicator in technical_indicators):
            return True
        
        # Default to no processing for better performance
        return False

    def answer(self,state:AgentState):
        agent_data=state.get('agent_data')
        name = agent_data.action.name
        params = agent_data.action.params
        
        # OPTIMIZATION: Minimal status update
        self.show_status("Finalizing", name, "Preparing response")
        
        # Cooperative pause checkpoint before final answer execution
        self._wait_if_paused("answer")
        
        tool_result = self.registry.execute(tool_name=name, desktop=None, **params)
        
        # OPTIMIZATION: Smart conversational processing only when needed
        if name == 'Done Tool':
            original_query = state.get('input', '')
            
            # Only process if response would benefit from conversational conversion
            if self._should_use_conversational_processing(tool_result.content, original_query):
                try:
                    conversational_response = self._make_conversational(tool_result.content, original_query)
                    tool_result.content = conversational_response
                except Exception as e:
                    logger.warning(f"Conversational processing failed: {e}. Using original response.")
                    # Keep original response if processing fails
        
        ai_message = AIMessage(content=Prompt.answer_prompt(agent_data=agent_data, tool_result=tool_result))
        
        # Log final answer to file
        agent_logger.log_final_answer(tool_result.content)
        
        # Show final answer (skip if it's a question for user)
        if not (name == 'Human Tool'):
            logger.info(colored(f"\n{tool_result.content}",color='cyan'))
        
        # Speak the response if TTS is enabled (Done Tool only, not questions)
        if self.tts_service and tool_result.content and name == 'Done Tool':
            self._speak_response(tool_result.content)
        
        return {**state,'agent_data':None,'messages':[ai_message],'previous_observation':None,'output':tool_result.content}

    def _make_conversational(self, raw_answer: str, original_query: str) -> str:
        """Convert raw answer to conversational response using LLM"""
        conversational_prompt = f"""You are a helpful assistant. Convert this raw response into a natural, conversational answer as if you're talking to a friend. Be warm, friendly, and human-like.

User asked: "{original_query}"
Raw answer: "{raw_answer}"

Guidelines:
- Sound natural and conversational, like you're talking to someone you know
- Don't use bullet points, numbered lists, or structured formats unless the information really needs it
- Be specific but natural - include the actual details from the raw answer
- Use contractions and casual language where appropriate 
- Add context or brief explanations to make it more helpful
- If it's a list of things (like tabs, files, etc.), present them in a flowing, conversational way

Examples of good conversational responses:
- Instead of: "Tab 1: Gmail, Tab 2: GitHub, Tab 3: Twitter"  
- Say: "You've got 3 tabs open right now - your Gmail inbox, a GitHub repository, and Twitter"

- Instead of: "File saved successfully. Location: C:\\Users\\Documents\\file.txt"
- Say: "Perfect! I've saved your file to the Documents folder as file.txt"

Convert the raw answer above into a natural, conversational response:"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=conversational_prompt)])
            conversational_result = response.content.strip()
            return conversational_result
            
        except Exception as e:
            logger.error(f"Failed to make response conversational: {e}")
            logger.warning("Falling back to original response")
            return raw_answer  # Fallback to original

    def _speak_response(self, text: str):
        """
        Speak the agent's response using TTS
        
        Args:
            text: Text to speak
        """
        if not self.tts_service or not text or not text.strip():
            return
            
        try:
            # Clean up the text for better speech (remove markdown, special characters, etc.)
            clean_text = self._clean_text_for_speech(text)
            
            if clean_text:
                # Log TTS output
                agent_logger.log_tts(clean_text)
                # Speak asynchronously to not block the main thread
                self.tts_service.speak_async(clean_text)
                
        except Exception as e:
            logger.error(f"Failed to speak response: {e}")

    def _clean_text_for_speech(self, text: str) -> str:
        """
        Clean text for better speech output
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text suitable for speech
        """
        if not text:
            return ""
            
        # Remove markdown formatting
        import re
        # Remove markdown bold/italic
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        # Remove code blocks
        text = re.sub(r'```.*?```', '[code block]', text, flags=re.DOTALL)
        # Remove inline code
        text = re.sub(r'`(.*?)`', r'\1', text)
        # Remove links
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # Remove headers
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Normalize text for natural speech
        text = self._normalize_for_speech(text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Limit length for better speech (avoid very long responses)
        if len(text) > 500:
            # Find a good breaking point
            sentences = text.split('. ')
            if len(sentences) > 1:
                # Take first few sentences
                text = '. '.join(sentences[:3])
                if not text.endswith('.'):
                    text += '.'
            else:
                # If no sentence breaks, just truncate
                text = text[:500] + "..."
        
        return text
    
    def _normalize_for_speech(self, text: str) -> str:
        """
        Normalize text for natural speech - convert symbols, numbers, etc.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        import re
        
        # Remove or replace punctuation that sounds bad when read aloud
        text = text.replace(',', '')  # Remove commas - natural pauses happen anyway
        text = text.replace(';', ',')  # Replace semicolons with pause
        text = text.replace(':', ' -')  # Replace colons with dash
        
        # Convert file sizes to spoken form
        text = re.sub(r'(\d+(?:\.\d+)?)\s*(GB|MB|KB|TB)', lambda m: self._number_to_words(float(m.group(1))) + ' ' + self._size_unit_to_words(m.group(2)), text, flags=re.IGNORECASE)
        
        # Convert percentages
        text = re.sub(r'(\d+(?:\.\d+)?)\s*%', lambda m: self._number_to_words(float(m.group(1))) + ' percent', text)
        
        # Convert standalone numbers with decimals to words
        text = re.sub(r'\b(\d+)\.(\d+)\b', lambda m: self._number_to_words(float(m.group(0))), text)
        
        # Convert large integers to words (only if they're not part of IDs or codes)
        text = re.sub(r'\b(\d{1,3})\b(?!\d)', lambda m: self._number_to_words(int(m.group(1))), text)
        
        # Handle common abbreviations
        abbreviations = {
            'URL': 'U R L',
            'URLs': 'U R Ls',
            'API': 'A P I',
            'UI': 'U I',
            'ID': 'I D',
            'CPU': 'C P U',
            'GPU': 'G P U',
            'RAM': 'R A M',
            'SSD': 'S S D',
            'HDD': 'H D D',
            'USB': 'U S B',
            'PDF': 'P D F',
            'HTML': 'H T M L',
            'CSS': 'C S S',
            'JS': 'javascript',
        }
        
        for abbr, spoken in abbreviations.items():
            text = re.sub(r'\b' + abbr + r'\b', spoken, text, flags=re.IGNORECASE)
        
        return text
    
    def _number_to_words(self, number: float) -> str:
        """
        Convert a number to words for speech
        
        Args:
            number: Number to convert
            
        Returns:
            Number in words
        """
        # Handle decimals
        if isinstance(number, float) and number != int(number):
            integer_part = int(number)
            decimal_part = str(number).split('.')[1]
            
            # For small decimals like 21.6
            if len(decimal_part) <= 2:
                return f"{self._int_to_words(integer_part)} point {self._int_to_words(int(decimal_part))}"
            else:
                # For longer decimals, just say the digits
                decimal_words = ' '.join([self._digit_to_word(d) for d in decimal_part])
                return f"{self._int_to_words(integer_part)} point {decimal_words}"
        
        return self._int_to_words(int(number))
    
    def _int_to_words(self, n: int) -> str:
        """Convert integer to words"""
        if n == 0:
            return "zero"
        
        ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
        teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        
        if n < 10:
            return ones[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
        elif n < 1000:
            return ones[n // 100] + " hundred" + (" " + self._int_to_words(n % 100) if n % 100 != 0 else "")
        elif n < 1000000:
            return self._int_to_words(n // 1000) + " thousand" + (" " + self._int_to_words(n % 1000) if n % 1000 != 0 else "")
        else:
            return str(n)  # For very large numbers, just return as string
    
    def _digit_to_word(self, digit: str) -> str:
        """Convert a single digit to word"""
        digits = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
        return digits[int(digit)] if digit.isdigit() else digit
    
    def _size_unit_to_words(self, unit: str) -> str:
        """Convert size units to spoken words"""
        units = {
            'GB': 'gigabytes',
            'MB': 'megabytes',
            'KB': 'kilobytes',
            'TB': 'terabytes',
            'gb': 'gigabytes',
            'mb': 'megabytes',
            'kb': 'kilobytes',
            'tb': 'terabytes',
        }
        return units.get(unit, unit)

    def stop_speaking(self):
        """Stop current speech if any"""
        if self.tts_service:
            self.tts_service.stop_current_speech()

    def is_speaking(self) -> bool:
        """Check if agent is currently speaking"""
        return self.tts_service and self.tts_service.is_busy()

    def main_controller(self,state:AgentState):
        if state.get('steps')<state.get('max_steps'):
            agent_data=state.get('agent_data')
            action_name=agent_data.action.name
            if action_name=='Human Tool':
                # Stop execution and wait for user response
                return 'answer'
            elif action_name!='Done Tool':
                return 'action'
        return 'answer'    

    def create_graph(self):
        graph=StateGraph(AgentState)
        graph.add_node('reason',self.reason)
        graph.add_node('action',self.action)
        graph.add_node('answer',self.answer)

        graph.add_edge(START,'reason')
        graph.add_conditional_edges('reason',self.main_controller)
        graph.add_edge('action','reason')
        graph.add_edge('answer',END)

        return graph.compile(debug=False)

    @timed("invoke")
    def invoke(self,query: str)->AgentResult:
        # Log user query to file
        agent_logger.log_user_query(query)
        
        # Show initial status
        self.show_status("Starting", "Task Analysis", f"Processing: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
        
        # Reset current task steps for memory tracking (disabled)
        self.current_task_steps = []
        
        # Check memory for similar tasks (disabled)
        # memory_hit = self.check_memory(query)
        
        steps=1
        
        # Parallel execution of independent operations for faster startup
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit parallel tasks
            desktop_future = executor.submit(self.desktop.get_state, self.use_vision)
            language_future = executor.submit(self.desktop.get_default_language)
            tools_future = executor.submit(self.registry.get_tools_prompt)
            
            # Collect results
            desktop_state = desktop_future.result()
            language = language_future.result()
            tools_prompt = tools_future.result()
        
        # Create or reuse system message
        if self.system_message is None or not self.enable_conversation:
            # Add running programs context to instructions
            additional_instructions = self.instructions.copy() if self.instructions else []
            
            # Add running programs context if available
            if hasattr(self, 'running_programs') and self.running_programs:
                programs_text = "Currently running programs:\n"
                grouped = {}
                for prog in self.running_programs:
                    name = prog['name']
                    if name not in grouped:
                        grouped[name] = []
                    grouped[name].append(prog)
                
                for name, instances in grouped.items():
                    programs_text += f"- {name.title()}\n"
                    for instance in instances:
                        if instance['title'] and instance['title'] != name:
                            programs_text += f"  * {instance['title']}\n"
                
                additional_instructions.append(f"RUNNING PROGRAMS CONTEXT:\n{programs_text}\nUse this information to avoid launching duplicate applications. If a program is already running, use Switch Tool instead of Launch Tool.")
            
            system_prompt=Prompt.system_prompt(browser=self.browser,language=language,instructions=additional_instructions,tools_prompt=tools_prompt,max_steps=self.max_steps,literal_mode=self.literal_mode)
            self.system_message=SystemMessage(content=system_prompt)
        
        # Add conversation context if enabled
        if self.enable_conversation and self.conversation_history:
            conversation_summary = self.get_conversation_summary()
            context_prompt = f"\n\n{conversation_summary}\n\nCurrent query: {query}"
        else:
            context_prompt = query
            
        human_prompt=Prompt.observation_prompt(query=context_prompt,steps=steps,max_steps=self.max_steps,tool_result=ToolResult(is_success=True, content="Desktop ready to operate."), desktop_state=desktop_state)
        human_message=image_message(prompt=human_prompt,image=desktop_state.screenshot) if self.use_vision and desktop_state.screenshot else HumanMessage(content=human_prompt)
        
        # Build messages with conversation history
        if self.enable_conversation:
            messages = [self.system_message] + self.conversation_history + [human_message]
        else:
            messages = [self.system_message, human_message]
        state={
            'input':query,
            'steps':steps,
            'max_steps':self.max_steps,
            'output':'',
            'error':'',
            'consecutive_failures':0,
            'agent_data':None,
            'messages':messages,
            'previous_observation':None
        }
        try:
            # Ensure COM initialized in this thread (Agent graph may use threads internally)
            try:
                ctypes.windll.ole32.CoInitializeEx(0, 2)
            except Exception:
                pass
            response=self.graph.invoke(state,config={'recursion_limit':self.max_steps*10})         
        except Exception as error:
            response={
                'output':None,
                'error':f"Error: {error}"
            }
        
        # Add to conversation history if enabled
        if self.enable_conversation:
            self.conversation_history.append(human_message)
            if response.get('output'):
                # Add the final AI response to conversation history
                final_ai_message = AIMessage(content=response['output'])
                self.conversation_history.append(final_ai_message)
        
        # Save successful task to memory (disabled)
        # if response.get('output') and self.current_task_steps:
        #     # Extract tags from the query (simple keyword extraction)
        #     query_lower = query.lower()
        #     tags = []
        #     if 'brightness' in query_lower or 'monitor' in query_lower:
        #         tags.append('monitor')
        #     if 'twinkle' in query_lower or 'tray' in query_lower:
        #         tags.append('twinkle-tray')
        #     if 'chrome' in query_lower or 'browser' in query_lower:
        #         tags.append('browser')
        #     if 'notepad' in query_lower or 'text' in query_lower:
        #         tags.append('text-editor')
        #     
        #     self.save_successful_task(query, self.current_task_steps, tags)
        
        
        return AgentResult(content=response['output'], error=response['error'])

    def print_response(self,query: str):
        response=self.invoke(query)
        self.console.print(Markdown(response.content or response.error))
    
    def print_response_with_context(self,query: str):
        """Print response with conversation context"""
        if self.enable_conversation and self.conversation_history:
            self.console.print("[bold blue]Previous conversation context:[/bold blue]")
            self.console.print(self.get_conversation_summary())
            self.console.print()
        
        response=self.invoke(query)
        self.console.print(Markdown(response.content or response.error))
    
    def cleanup(self):
        """Clean up agent resources including TTS service"""
        if self.tts_service:
            self.tts_service.cleanup()   