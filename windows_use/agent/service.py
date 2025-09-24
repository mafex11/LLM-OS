from windows_use.agent.tools.service import click_tool, type_tool, launch_tool, shell_tool, clipboard_tool, done_tool, shortcut_tool, scroll_tool, drag_tool, move_tool, key_tool, wait_tool, scrape_tool, switch_tool, resize_tool, human_tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from windows_use.agent.utils import extract_agent_data, image_message
from langchain_core.language_models.chat_models import BaseChatModel
# from windows_use.agent.ollama_client import OllamaChat
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from windows_use.agent.registry.views import ToolResult
from windows_use.agent.registry.service import Registry
from windows_use.agent.prompt.service import Prompt
from windows_use.agent.memory import MemoryManager
from windows_use.agent.performance import PerformanceMonitor, timed
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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    def __init__(self,instructions:list[str]=[],additional_tools:list[BaseTool]=[],browser:Literal['edge','chrome','firefox']='edge', llm: BaseChatModel=None,consecutive_failures:int=3,max_steps:int=20,use_vision:bool=False,enable_conversation:bool=True,literal_mode:bool=True):
        self.name='Windows Use'
        self.description='An agent that can interact with GUI elements on Windows' 
        self.registry = Registry([
            click_tool,type_tool, launch_tool, shell_tool, clipboard_tool,
            done_tool, shortcut_tool, scroll_tool, drag_tool, move_tool,
            key_tool, wait_tool, scrape_tool, switch_tool, resize_tool, human_tool
        ] + additional_tools)
        self.instructions=instructions
        self.browser=browser
        self.max_steps=max_steps
        self.consecutive_failures=consecutive_failures
        self.use_vision=use_vision
        self.enable_conversation=enable_conversation
        self.literal_mode=literal_mode
        # self.llm = llm or OllamaChat(model="gemma3:latest")
        self.llm = llm or ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
        self.watch_cursor = WatchCursor()
        self.desktop = Desktop()
        self.console=Console(file=sys.stderr)  # Use stderr to avoid interfering with stdin
        self.graph=self.create_graph()
        # Conversation history
        self.conversation_history = []
        self.system_message = None
        # Memory management
        self.memory_manager = MemoryManager()
        self.current_task_steps = []  # Track steps for current task
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()

    def clear_conversation(self):
        """Clear the conversation history"""
        self.conversation_history = []
        self.system_message = None
        
    
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
        """Check if we have a memory for this query"""
        solution_steps = self.memory_manager.get_memory_solution(query)
        if solution_steps:
            self.console.print(f"[bold green]Found memory for similar task![/bold green]")
            self.console.print(f"[dim]Previous solution had {len(solution_steps)} steps[/dim]")
            return f"Found previous solution with {len(solution_steps)} steps. Applying known solution..."
        return ""

    def save_successful_task(self, query: str, steps: list, tags: list = None):
        """Save a successful task solution to memory"""
        if steps:
            key = self.memory_manager.add_memory(query, steps, tags)
            self.console.print(f"[bold green]Saved solution to memory (ID: {key})[/bold green]")

    def get_memory_stats(self) -> dict:
        """Get memory statistics"""
        return self.memory_manager.get_memory_stats()

    def list_memories(self) -> list:
        """List all stored memories"""
        return self.memory_manager.list_memories()

    def clear_memories(self):
        """Clear all memories"""
        self.memory_manager.clear_memories()
        self.console.print("[bold yellow]All memories cleared[/bold yellow]")

    def show_status(self, status: str, action_name: str = None, details: str = None):
        """Display real-time status updates"""
        if action_name:
            self.console.print(f"[bold blue]{status}[/bold blue] - [cyan]{action_name}[/cyan]")
            if details:
                self.console.print(f"   [dim]{details}[/dim]")
        else:
            self.console.print(f"[bold blue]{status}[/bold blue]")
            

    @timed("reason")
    def reason(self,state:AgentState):
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
        logger.info(f"Iteration: {steps}")
        agent_data = extract_agent_data(message=message)
        logger.info(colored(f"Evaluate: {agent_data.evaluate}",color='yellow',attrs=['bold']))
        logger.info(colored(f"Memory: {agent_data.memory}",color='light_green',attrs=['bold']))
        logger.info(colored(f"Plan: {agent_data.plan}",color='light_blue',attrs=['bold']))
        logger.info(colored(f"Thought: {agent_data.thought}",color='light_magenta',attrs=['bold']))
        last_message = state.get('messages').pop()
        if isinstance(last_message, HumanMessage):
            message=HumanMessage(content=Prompt.previous_observation_prompt(steps=steps,max_steps=max_steps,observation=state.get('previous_observation')))
            return {**state,'agent_data':agent_data,'messages':[message],'steps':steps+1}

    @timed("action")
    def action(self,state:AgentState):
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
        
        logger.info(colored(f"Action: {name}({', '.join(f'{k}={v}' for k, v in params.items())})",color='blue',attrs=['bold']))
        tool_result = self.registry.execute(tool_name=name, desktop=self.desktop, **params)
        observation=tool_result.content if tool_result.is_success else tool_result.error
        
        # Track step for memory (only for successful actions that aren't Done Tool)
        if tool_result.is_success and name != 'Done Tool':
            step_info = {
                'action': name,
                'params': params,
                'result': observation
            }
            self.current_task_steps.append(step_info)
        
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
        
        logger.info(colored(f"Observation: {shorten(observation,500,placeholder='...')}",color='green',attrs=['bold']))
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

    def answer(self,state:AgentState):
        agent_data=state.get('agent_data')
        name = agent_data.action.name
        params = agent_data.action.params
        
        # Show final answer status
        self.show_status("Finalizing", name, "Preparing final response")
        
        tool_result = self.registry.execute(tool_name=name, desktop=None, **params)
        
        # NEW: If this is a Done Tool, process the response conversationally
        if name == 'Done Tool':
            original_query = state.get('input', '')
            conversational_response = self._make_conversational(tool_result.content, original_query)
            tool_result.content = conversational_response
        
        ai_message = AIMessage(content=Prompt.answer_prompt(agent_data=agent_data, tool_result=tool_result))
        
        # Show completion
        self.show_status("Done", "Task Complete", "All actions completed")
        
        logger.info(colored(f"Final Answer: {tool_result.content}",color='cyan',attrs=['bold']))
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
            
            # Log the conversion for debugging
            logger.info(colored(f"Conversational processing:", color='yellow'))
            logger.info(colored(f"   Raw: {raw_answer[:100]}{'...' if len(raw_answer) > 100 else ''}", color='yellow'))
            logger.info(colored(f"   Conversational: {conversational_result[:100]}{'...' if len(conversational_result) > 100 else ''}", color='yellow'))
            
            return conversational_result
            
        except Exception as e:
            logger.error(f"Failed to make response conversational: {e}")
            logger.warning("Falling back to original response")
            return raw_answer  # Fallback to original

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
        # Show initial status
        self.show_status("Starting", "Task Analysis", f"Processing: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
        
        # Reset current task steps for memory tracking
        self.current_task_steps = []
        
        # Check memory for similar tasks
        memory_hit = self.check_memory(query)
        
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
            with self.desktop.auto_minimize():
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
        
        # Save successful task to memory if it completed successfully
        if response.get('output') and self.current_task_steps:
            # Extract tags from the query (simple keyword extraction)
            query_lower = query.lower()
            tags = []
            if 'brightness' in query_lower or 'monitor' in query_lower:
                tags.append('monitor')
            if 'twinkle' in query_lower or 'tray' in query_lower:
                tags.append('twinkle-tray')
            if 'chrome' in query_lower or 'browser' in query_lower:
                tags.append('browser')
            if 'notepad' in query_lower or 'text' in query_lower:
                tags.append('text-editor')
            
            self.save_successful_task(query, self.current_task_steps, tags)
        
        
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