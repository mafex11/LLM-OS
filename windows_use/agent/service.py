from windows_use.agent.tools.service import click_tool, type_tool, launch_tool, shell_tool, clipboard_tool, done_tool, shortcut_tool, scroll_tool, drag_tool, move_tool, key_tool, wait_tool, scrape_tool, switch_tool, resize_tool, human_tool, system_tool, schedule_tool
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
    Yuki AI

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
    def __init__(self,instructions:list[str]=[],additional_tools:list[BaseTool]=[],browser:Literal['edge','chrome','firefox']='edge', llm: BaseChatModel=None,consecutive_failures:int=3,max_steps:int=20,use_vision:bool=False,enable_conversation:bool=True,literal_mode:bool=True,enable_tts:bool=False,tts_voice_id:str="21m00Tcm4TlvDq8ikWAM",enable_screenshot_analysis:bool=True,enable_activity_tracking:bool=True):
        self.name='Yuki AI'
        self.description='An agent that can interact with GUI elements on Windows' 
        from windows_use.agent.tools.service import activity_tool, timeline_tool
        self.registry = Registry([
            click_tool,type_tool, launch_tool, shell_tool, clipboard_tool,
            done_tool, shortcut_tool, scroll_tool, drag_tool, move_tool,
            key_tool, wait_tool, scrape_tool, switch_tool, resize_tool, human_tool, system_tool, schedule_tool, activity_tool, timeline_tool
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
        self.enable_screenshot_analysis=enable_screenshot_analysis
        self.enable_activity_tracking=enable_activity_tracking
        self.llm = llm or ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
        self.model_id = getattr(self.llm, "model", "gemini-2.0-flash")
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
        # Cooperative stop controller
        self._stop_event = threading.Event()
        self._stop_event.clear()
        # Activity tracking
        self.activity_tracker = None
        self.screenshot_service = None
        self.activity_analyzer = None
        self.notification_callback = None  # Notification callback for activity tracking
        # Track the target app for precise detection (e.g., Calculator after switching to it)
        self._target_app_for_precise_detection = None
        self._initialize_tracking()

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

    def stop(self):
        """Request a cooperative stop. Execution will abort at the next checkpoint."""
        self._stop_event.set()
        # Also unpause if paused so checkpoints can notice stop promptly
        with self._pause_lock:
            self._pause_event.clear()

    def is_stopped(self) -> bool:
        """Check if a stop was requested."""
        return self._stop_event.is_set()

    def _check_stop(self):
        """Raise an exception if stop was requested to abort execution quickly."""
        if self._stop_event.is_set():
            raise RuntimeError("Execution stopped by user")

    def _wait_if_paused(self, checkpoint_name: str = ""):
        """Block cooperatively while paused, emitting a status message once."""
        # Always check for stop first
        self._check_stop()
        if not self._pause_event.is_set():
            return
        # Announce pause once per checkpoint entry
        self.show_status("Paused", "Stop/Wait", f"Waiting at checkpoint: {checkpoint_name}")
        # Spin-wait cooperatively with small sleeps to reduce CPU
        while self._pause_event.is_set():
            # Allow stop during pause
            if self._stop_event.is_set():
                raise RuntimeError("Execution stopped by user")
            time.sleep(0.05)

    def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []
        self.system_message = None
        agent_logger.log_conversation_cleared()
        
    
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
        # Abort early if stop requested
        self._check_stop()
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
                    fresh_desktop_state = self.desktop.get_state(use_vision=self.use_vision)
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
        # Abort early if stop requested
        self._check_stop()
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
        # CRITICAL: Use precise detection if we have a target app (e.g., Calculator)
        # IMPORTANT: If we just switched/launched an app, the state should already be fresh
        # Only refresh if state is truly stale (> 1.5s old) to avoid capturing wrong window
        # CRITICAL: Ensure target app is in foreground before refreshing to get correct coordinates
        if name in ['Click Tool', 'Type Tool', 'Scroll Tool', 'Drag Tool', 'Move Tool']:
            current_time = time.time()
            state_age = current_time - getattr(self.desktop, '_last_state_time', 0) if hasattr(self.desktop, '_last_state_time') else float('inf')
            
            # Only refresh if state is stale (older than 1.5s)
            # This prevents refreshing right after switching, which could capture wrong window
            if state_age > 1.5:
                # Use precise detection if we have a target app
                target_app = self._target_app_for_precise_detection
                if target_app:
                    # CRITICAL: Verify target app is actually in foreground before getting elements
                    # If not, try to switch to it first
                    if self.desktop.desktop_state and self.desktop.desktop_state.active_app:
                        active_app_name = self.desktop.desktop_state.active_app.name.lower()
                        target_app_lower = target_app.lower()
                        if not (target_app_lower in active_app_name or active_app_name in target_app_lower):
                            # Target app is not in foreground - try to switch to it
                            self.show_status("Warning", "Focus", f"Target app {target_app} not in foreground, switching to it")
                            try:
                                switch_result, switch_status = self.desktop.switch_app(target_app)
                                if switch_status == 0:
                                    time.sleep(0.3)  # Wait for switch to complete
                                else:
                                    self.show_status("Warning", "Focus", f"Failed to switch to {target_app}: {switch_result}")
                            except Exception as e:
                                self.show_status("Warning", "Focus", f"Error switching to {target_app}: {e}")
                    
                    # Now get state with precise detection
                    self.desktop.get_state(use_vision=self.use_vision, target_app=target_app)
                    self.show_status("Refreshing", "Desktop State", f"Getting precise coordinates for {target_app}")
                else:
                    self.desktop.get_state(use_vision=self.use_vision)
                    self.show_status("Refreshing", "Desktop State", "Getting updated coordinates")
                self.desktop._last_state_time = current_time
            else:
                # State is fresh - verify target app is still active
                if self._target_app_for_precise_detection and self.desktop.desktop_state and self.desktop.desktop_state.active_app:
                    active_app_name = self.desktop.desktop_state.active_app.name.lower()
                    target_app_lower = self._target_app_for_precise_detection.lower()
                    if not (target_app_lower in active_app_name or active_app_name in target_app_lower):
                        # Target app lost focus - try to switch back and refresh with precise detection
                        self.show_status("Warning", "Focus", f"Target app lost focus, switching back to {self._target_app_for_precise_detection}")
                        try:
                            switch_result, switch_status = self.desktop.switch_app(self._target_app_for_precise_detection)
                            if switch_status == 0:
                                time.sleep(0.3)  # Wait for switch to complete
                                self.desktop.get_state(use_vision=self.use_vision, target_app=self._target_app_for_precise_detection)
                                self.show_status("Refreshing", "Desktop State", f"Target app lost focus, refreshed precise coordinates")
                            else:
                                self.show_status("Warning", "Focus", f"Failed to switch: {switch_result}")
                                # Still refresh to get current state
                                self.desktop.get_state(use_vision=self.use_vision, target_app=self._target_app_for_precise_detection)
                        except Exception as e:
                            self.show_status("Warning", "Focus", f"Error switching: {e}")
                            self.desktop.get_state(use_vision=self.use_vision, target_app=self._target_app_for_precise_detection)
                        self.desktop._last_state_time = current_time
        
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
        # Launch Tool may switch to existing app or launch new one - handle both cases
        if tool_result.is_success and name == 'Launch Tool':
            # Extract app name from launch params
            launched_app = params.get('name', '').strip() if 'name' in params else None
            
            # Check if Launch Tool switched to existing app (response contains "already running" or "switched")
            was_switch = 'already running' in observation.lower() or 'switched' in observation.lower()
            
            if launched_app:
                # Check if this app supports precise detection (Calculator, browsers, etc.)
                apps_with_precise_detection = [
                    'calculator',
                    'calc',
                    'chrome',
                    'google chrome',
                    'edge',
                    'microsoft edge',
                    'firefox',
                    'mozilla firefox'
                ]
                if any(app in launched_app.lower() for app in apps_with_precise_detection):
                    self._target_app_for_precise_detection = launched_app
                    if was_switch:
                        # App was already running and we switched to it - wait a bit then use precise detection
                        time.sleep(0.3)  # Wait for switch to complete
                        self.show_status("Refreshing", "Desktop State", f"Getting precise coordinates for {launched_app} after switch")
                        self.desktop.get_state(use_vision=self.use_vision, target_app=launched_app)
                    else:
                        # New app was launched - wait for it to load then use precise detection
                        time.sleep(0.2)  # Wait for app to stabilize
                        self.show_status("Refreshing", "Desktop State", f"Getting precise coordinates for {launched_app} after launch")
                        self.desktop.get_state(use_vision=self.use_vision, target_app=launched_app)
                else:
                    # App doesn't support precise detection - use regular detection
                    if was_switch:
                        time.sleep(0.3)  # Wait for switch to complete
                    else:
                        time.sleep(0.2)  # Wait for app to load
                    self.desktop.get_state(use_vision=self.use_vision)
                    self.show_status("Refreshing", "Desktop State", "Getting fresh coordinates after launch")
            else:
                self.desktop.get_state(use_vision=self.use_vision)
                self.show_status("Refreshing", "Desktop State", "Getting fresh coordinates after launch")
            self.desktop._last_state_time = time.time()
        
        # Cooperative pause checkpoint after action side-effects settle
        self._wait_if_paused("action:end")
        
        # Log observation to file
        agent_logger.log_observation(observation)
        
        # Show observation (skip for Human Tool as it's a question)
        if name != 'Human Tool':
            logger.info(colored(f"{shorten(observation,500,placeholder='...')}",color='green'))
        
        # Smart desktop state refresh: Only refresh when needed
        # Actions that don't need immediate state refresh (they don't change UI coordinates):
        # - Key Tool: Just presses keys, UI doesn't change structure - reuse state to avoid focus shifts
        # - Done Tool: Task complete, no next action needed
        # - Wait Tool: Just waits, no UI change
        # - Human Tool: Asking user, no UI change
        
        # Special handling for Switch Tool: After switching, wait for switch to complete,
        # then refresh state to get accurate foreground app info using PRECISE DETECTION
        if name == 'Switch Tool' and tool_result.is_success:
            # Wait longer for the window switch to fully complete and stabilize
            # The switch_app method keeps the window topmost for ~150ms after confirmation,
            # so we wait a bit more to ensure it's ready for detection
            time.sleep(0.3)  # 300ms to ensure switch is fully complete
            
            # Extract app name from switch params and use precise detection
            switched_app = params.get('name', '').strip() if 'name' in params else None
            if switched_app:
                # Check if this app supports precise detection (Calculator, browsers, etc.)
                apps_with_precise_detection = [
                    'calculator',
                    'calc',
                    'chrome',
                    'google chrome',
                    'edge',
                    'microsoft edge',
                    'firefox',
                    'mozilla firefox'
                ]
                if any(app in switched_app.lower() for app in apps_with_precise_detection):
                    self._target_app_for_precise_detection = switched_app
                    self.show_status("Refreshing", "Desktop State", f"Getting precise coordinates for {switched_app}")
                    desktop_state = self.desktop.get_state(use_vision=self.use_vision, target_app=switched_app)
                else:
                    # For other apps, use regular detection but track the app name
                    self._target_app_for_precise_detection = None
                    desktop_state = self.desktop.get_state(use_vision=self.use_vision)
                    self.show_status("Refreshing", "Desktop State", "Getting updated coordinates after switch")
            else:
                desktop_state = self.desktop.get_state(use_vision=self.use_vision)
                self.show_status("Refreshing", "Desktop State", "Getting updated coordinates after switch")
            self.desktop._last_state_time = time.time()
        elif name in ['Key Tool', 'Done Tool', 'Wait Tool', 'Human Tool'] and tool_result.is_success:
            # For these actions, reuse existing desktop state without refreshing
            # This prevents focus shifts that cause unnecessary window switching
            # Key Tool especially: after pressing space to pause, we don't want to refresh
            # state immediately as it might cause focus to shift and make agent think it needs to switch again
            desktop_state = self.desktop.desktop_state
            if desktop_state is None:
                # Fallback: if no state exists, get it (shouldn't happen normally)
                desktop_state = self.desktop.get_state(use_vision=self.use_vision)
                self.desktop._last_state_time = time.time()
        else:
            # For other actions (Click, Type, Scroll, etc.), refresh if stale
            # Use precise detection if we have a target app
            current_time = time.time()
            if (not hasattr(self.desktop, '_last_state_time') or 
                current_time - getattr(self.desktop, '_last_state_time', 0) > 1.0):
                # Add small delay after actions to let UI settle before refreshing
                # This prevents focus shifts from state refresh interfering with the action
                if name not in ['Launch Tool']:  # Launch Tool already refreshed above
                    time.sleep(0.1)  # 100ms delay to let UI settle
                
                # Use precise detection if we have a target app and it's still active
                target_app = self._target_app_for_precise_detection
                if target_app and self.desktop.desktop_state and self.desktop.desktop_state.active_app:
                    active_app_name = self.desktop.desktop_state.active_app.name.lower()
                    if target_app.lower() in active_app_name or active_app_name in target_app.lower():
                        desktop_state = self.desktop.get_state(use_vision=self.use_vision, target_app=target_app)
                    else:
                        # Target app is no longer active, clear it
                        self._target_app_for_precise_detection = None
                        desktop_state = self.desktop.get_state(use_vision=self.use_vision)
                elif target_app:
                    # Use precise detection even if we don't have current state
                    desktop_state = self.desktop.get_state(use_vision=self.use_vision, target_app=target_app)
                else:
                    desktop_state = self.desktop.get_state(use_vision=self.use_vision)
                self.desktop._last_state_time = current_time
            else:
                desktop_state = self.desktop.desktop_state or self.desktop.get_state(use_vision=self.use_vision)
            
            # After clicking, check if we clicked outside the target app window
            # If so, clear the target app to avoid using stale coordinates
            if name == 'Click Tool' and tool_result.is_success:
                if self._target_app_for_precise_detection and desktop_state and desktop_state.active_app:
                    active_app_name = desktop_state.active_app.name.lower()
                    target_app_lower = self._target_app_for_precise_detection.lower()
                    if not (target_app_lower in active_app_name or active_app_name in target_app_lower):
                        # We clicked outside the target app, clear it
                        self._target_app_for_precise_detection = None
                        self.show_status("Warning", "Click", "Clicked outside target app, clearing precise detection")
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
        # Abort early if stop requested
        self._check_stop()
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
        
        # Check if this is an activity tracking query
        query_lower = query.lower().strip()
        activity_keywords = [
            "how focused", "did i do well", "how productive", "how much time",
            "what apps", "activity", "productivity", "focus score",
            "how long", "time spent", "today's activity", "my activity"
        ]
        
        if any(keyword in query_lower for keyword in activity_keywords) and self.activity_tracker:
            # Handle activity query directly
            try:
                from datetime import datetime
                import json
                
                # Get today's date
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Get activities and summary
                storage = self.activity_tracker.storage
                activities = storage.get_activities(today)
                summary = storage.get_daily_summary(today)
                
                # Generate summary if doesn't exist
                if not summary and self.activity_analyzer:
                    screenshots = storage.get_screenshot_metadata(today)
                    summary = self.activity_analyzer.calculate_daily_summary(activities, screenshots)
                    storage.save_daily_summary(summary)
                
                # Generate response using LLM
                if summary and self.llm:
                    prompt = f"""The user asked: "{query}"

Activity summary for {today}:
{json.dumps(summary, indent=2)}

Provide a natural, conversational response answering the user's question about their activity and productivity.
Be specific with numbers and insights. Be encouraging and helpful."""
                    
                    response = self.llm.invoke([HumanMessage(content=prompt)])
                    answer = response.content if hasattr(response, 'content') else str(response)
                    
                    return AgentResult(content=answer, error=None)
                elif summary:
                    # Fallback: generate simple response from summary
                    focus_score = summary.get("focus_score", 0)
                    work_time = summary.get("work_time", 0) / 3600
                    research_time = summary.get("research_time", 0) / 3600
                    insights = summary.get("insights", "Activity tracking is collecting data.")
                    
                    answer = f"Your focus score today is {focus_score}%. "
                    if work_time > 0:
                        answer += f"You spent {work_time:.1f} hours on work. "
                    if research_time > 0:
                        answer += f"You spent {research_time:.1f} hours on research. "
                    answer += insights
                    
                    return AgentResult(content=answer, error=None)
                else:
                    return AgentResult(
                        content="Activity tracking is enabled and collecting data. Please check back later for insights.",
                        error=None
                    )
            except Exception as e:
                logger.error(f"Error handling activity query: {e}")
                # Fall through to normal agent processing
        
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
    
    def _initialize_tracking(self):
        """Initialize activity tracking system."""
        # Check if activity tracking is disabled
        if not self.enable_activity_tracking:
            logger.info("Activity tracking is disabled in settings")
            self.activity_tracker = None
            self.screenshot_service = None
            self.activity_analyzer = None
            return
        
        try:
            from windows_use.tracking.config import initialize_tracking
            import os
            
            # Get Google API key for analyzer - try multiple sources
            google_api_key = None
            
            # Try to get from LLM instance if it's ChatGoogleGenerativeAI
            try:
                if isinstance(self.llm, ChatGoogleGenerativeAI):
                    # Check if API key is stored in the model
                    if hasattr(self.llm, 'google_api_key'):
                        google_api_key = self.llm.google_api_key
                    elif hasattr(self.llm, 'client') and hasattr(self.llm.client, '_client'):
                        # Try to extract from client
                        pass
            except Exception:
                pass
            
            # Fallback to environment variable
            if not google_api_key:
                google_api_key = os.getenv('GOOGLE_API_KEY')
            
            # Fallback: try to use the same LLM instance if available
            if not google_api_key and self.llm:
                # Pass the LLM instance directly to analyzer
                pass
            
            # Get storage path from environment
            # Use WINDOWS_USE_DATA_PATH (set by Electron) or fallback to YUKI_DATA_PATH or default
            storage_path = os.getenv('WINDOWS_USE_DATA_PATH') or os.getenv('YUKI_DATA_PATH') or os.path.join(os.getcwd(), 'data')
            
            # Use enable_screenshot_analysis setting to control screenshot capture and analysis
            enable_screenshots = self.enable_screenshot_analysis
            
            # Initialize tracking with screenshot analysis setting
            # Pass LLM instance for AI-based productivity classification
            if google_api_key:
                self.activity_tracker, self.screenshot_service, self.activity_analyzer = initialize_tracking(
                    desktop=self.desktop,
                    storage_path=storage_path,
                    google_api_key=google_api_key,
                    enable_screenshots=enable_screenshots,
                    screenshot_interval=300.0,  # 5 minutes
                    poll_interval=2.0,
                    notification_callback=self.notification_callback,
                    llm=self.llm if enable_screenshots else None  # Only pass LLM if screenshot analysis is enabled
                )
            else:
                # Initialize without API key - analyzer will try to use LLM instance
                self.activity_tracker, self.screenshot_service, self.activity_analyzer = initialize_tracking(
                    desktop=self.desktop,
                    storage_path=storage_path,
                    google_api_key=None,
                    enable_screenshots=enable_screenshots,
                    screenshot_interval=300.0,
                    poll_interval=2.0,
                    notification_callback=self.notification_callback,
                    llm=self.llm if enable_screenshots else None  # Only pass LLM if screenshot analysis is enabled
                )
                # Try to set LLM on analyzer if available and screenshot analysis is enabled
                if self.activity_analyzer and self.llm and enable_screenshots:
                    try:
                        self.activity_analyzer.llm = self.llm
                    except Exception:
                        pass
            
            # Start tracking
            if self.activity_tracker:
                self.activity_tracker.start_tracking()
            if self.screenshot_service and enable_screenshots:
                self.screenshot_service.start_capturing()
            
            logger.info(f"Activity tracking initialized and started (screenshot analysis: {enable_screenshots})")
        
        except Exception as e:
            logger.warning(f"Failed to initialize activity tracking: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            self.activity_tracker = None
            self.screenshot_service = None
            self.activity_analyzer = None
    
    def cleanup(self):
        """Clean up agent resources including TTS service and activity tracking"""
        if self.tts_service:
            self.tts_service.cleanup()
        
        # Stop activity tracking
        if self.activity_tracker:
            try:
                self.activity_tracker.stop_tracking()
            except Exception as e:
                logger.error(f"Error stopping activity tracker: {e}")
        
        if self.screenshot_service:
            try:
                self.screenshot_service.stop_capturing()
            except Exception as e:
                logger.error(f"Error stopping screenshot service: {e}")   