from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from windows_use.agent.stt_service import STTService, is_stt_available
from windows_use.agent.logger import agent_logger
from dotenv import load_dotenv
from rich.markdown import Markdown
import os
import subprocess
import json
import time
import argparse
import threading
import queue

# Import overlay functionality
# try:
#     from overlay_ui import start_overlay, stop_overlay
#     OVERLAY_AVAILABLE = True
# except ImportError:
#     OVERLAY_AVAILABLE = False
#     def start_overlay():
#         pass
#     def stop_overlay():
#         pass

# Overlay disabled
OVERLAY_AVAILABLE = False
def start_overlay():
    pass
def stop_overlay():
    pass

load_dotenv()

# Fix Windows console encoding issues - CRITICAL for special characters
import sys
if sys.platform == 'win32':
    # Force UTF-8 encoding for Windows console
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Set console code page to UTF-8
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)  # Input code page
        kernel32.SetConsoleOutputCP(65001)  # Output code page
    except:
        pass
    # Force stdout/stderr to use UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def safe_input(prompt="\nYou: "):
    """Safe input function that avoids pyreadline3 issues on Windows."""
    import sys
    import time
    import msvcrt
    
    # Force flush any pending output
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Small delay to ensure all output is processed
    time.sleep(0.1)
    
    try:
        # Try the standard input() first
        user_input = input(prompt).strip()
        return user_input if user_input else ""
        
    except (EOFError, KeyboardInterrupt):
        return "quit"
    except Exception as e:
        print(f"\nInput error: {e}")
        print("Falling back to alternative input method...")
        
        # Fallback: Use msvcrt for Windows console input
        try:
            print(prompt, end='', flush=True)
            user_input = ""
            while True:
                char = msvcrt.getch()
                if char == b'\r':  # Enter key
                    print()  # New line
                    break
                elif char == b'\x08':  # Backspace
                    if user_input:
                        user_input = user_input[:-1]
                        print('\b \b', end='', flush=True)
                elif char == b'\x03':  # Ctrl+C
                    return "quit"
                else:
                    try:
                        char_str = char.decode('utf-8')
                        user_input += char_str
                        print(char_str, end='', flush=True)
                    except UnicodeDecodeError:
                        pass  # Skip invalid characters
            
            return user_input.strip() if user_input else ""
            
        except Exception as fallback_error:
            print(f"\nFallback input also failed: {fallback_error}")
            return "quit"

def show_ready_indicator():
    """Show a visual indicator that the system is ready for input."""
    print("Ready for your next command...")

def get_running_programs():
    """Get list of currently running programs using PowerShell"""
    try:
        # PowerShell command to get running processes
        cmd = [
            "powershell", "-Command",
            "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object ProcessName, MainWindowTitle, Id | ConvertTo-Json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            processes = json.loads(result.stdout)
            if isinstance(processes, dict):
                processes = [processes]  # Convert single object to list
            
            # Filter and format the processes
            running_programs = []
            for proc in processes:
                if proc.get('MainWindowTitle'):
                    running_programs.append({
                        'name': proc.get('ProcessName', ''),
                        'title': proc.get('MainWindowTitle', ''),
                        'id': proc.get('Id', '')
                    })
            
            return running_programs
        else:
            print(f"Warning: Could not get running programs: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"Warning: Error getting running programs: {e}")
        return []

def display_running_programs(programs):
    """Display running programs in a formatted way"""
    if not programs:
        print("No programs with visible windows detected")
        return
    
    print("Currently Running Programs:")
    print("-" * 40)
    
    # Group by process name
    grouped = {}
    for prog in programs:
        name = prog['name']
        if name not in grouped:
            grouped[name] = []
        grouped[name].append(prog)
    
    for name, instances in grouped.items():
        print(f"• {name.title()}")
        for instance in instances:
            if instance['title'] and instance['title'] != name:
                print(f"  - {instance['title']}")
    
    print("-" * 40)

def run_voice_mode(agent):
    """Run agent in continuous voice listening mode with async task execution and trigger word detection"""
    print("\n🎤 Voice Mode Activated with Trigger Word Detection")
    print("=" * 50)
    
    # Initialize STT service with trigger word
    print("Initializing Deepgram STT with 'yuki' trigger word...")
    stt_service = STTService(enable_stt=True, trigger_word="yuki")
    
    if not stt_service.enabled:
        print("ERROR: Deepgram STT is not available!")
        print("Please ensure:")
        print("1. DEEPGRAM_API_KEY is set in your .env file")
        print("2. deepgram-sdk is installed: pip install deepgram-sdk")
        print("\nFalling back to text input mode...")
        return False
    
    print("STT Status: Enabled and ready")
    print("STT Service initialized with balanced latency mode")
    print("\n🎤 Voice Commands with Trigger Word:")
    print("  - Say 'yuki' followed by your command (e.g., 'yuki, open my calendar')")
    print("  - Only commands preceded by 'yuki' will be processed")
    print("  - Say 'yuki' alone to activate command mode, then speak your command")
    print("  - Say 'switch to text' to switch to keyboard input")
    print("  - Say 'clear conversation' to clear history")
    print("  - Say 'quit' or 'exit' to exit")
    print("=" * 50)
    
    # Task execution state
    task_thread = None
    task_running = False
    task_lock = threading.Lock()
    mid_query_queue = queue.Queue()
    switch_to_text = False
    
    def run_task_async(task_query: str):
        """Run a task in background thread with pause support"""
        nonlocal task_running
        try:
            with task_lock:
                task_running = True
            
            print(f"\n🤖 Working on: {task_query[:50]}{'...' if len(task_query) > 50 else ''}")
            
            # Execute the agent task
            response = agent.invoke(task_query)
            
            # Handle response
            try:
                content = response.content or response.error or "No response"
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='replace')
                
                # Check if it's a question for user
                if "Human Tool" in str(response):
                    question = content.strip()
                    print(f"\n{question}")
                    
                    # Speak the question if TTS is enabled
                    if agent.tts_service and agent.tts_service.enabled:
                        agent.tts_service.speak_async(question)
                    
                    print("\n🎤 Listening for your answer...")
                # Response is already printed by agent service
                
            except Exception:
                safe = (response.content or response.error or "No response")
                safe = safe.encode('ascii', errors='ignore').decode('ascii')
                print(f"\n{safe}")
                
        finally:
            # Mark task as finished and ensure agent is resumed
            agent.resume()
            with task_lock:
                task_running = False
            try:
                # Refresh desktop state to avoid stale UI after task actions
                agent.desktop.get_state(use_vision=False)
            except Exception:
                pass
            print("\n✅ Task completed!")
            print("🎤 Listening for your next command...")
            sys.stdout.flush()
            sys.stderr.flush()
    
    def answer_mid_query(q: str):
        """Answer a user query conversationally without executing a new task"""
        try:
            # Build a light conversational prompt using recent context
            context = agent.get_conversation_summary() if agent.enable_conversation else ""
            prompt = (
                f"You are in Chat mode. Answer the user's question briefly and conversationally. "
                f"Do not perform any actions or use tools - just provide information.\n\n"
                f"Context:\n{context}\n\nQuestion: {q}"
            )
            from langchain_core.messages import HumanMessage
            result = agent.llm.invoke([HumanMessage(content=prompt)])
            answer_text = getattr(result, 'content', None) or str(result)
            
            # Print the answer
            print(f"\n💬 {answer_text}\n")
            
            # Speak the answer if TTS is enabled
            if agent.tts_service and agent.tts_service.enabled:
                agent.tts_service.speak_async(answer_text)
                
        except Exception as e:
            answer_text = f"(Failed to answer: {e})"
            print(f"\n{answer_text}\n")
    
    def on_transcription(transcript: str):
        """Callback when transcription is received (only triggered commands after 'yuki')"""
        nonlocal switch_to_text, task_thread
        
        # Check if we're waiting for a command after trigger word detection
        if stt_service.is_waiting_for_command():
            print(f"\n🎤 Command received: {transcript}")
            print("🎤 Listening for your next command...")
        else:
            print(f"\n🎤 Trigger word detected, command received: {transcript}")
        
        # Log STT input
        agent_logger.log_stt(transcript)
        
        # Check for mode switch command
        if 'switch to text' in transcript.lower() or 'text mode' in transcript.lower():
            switch_to_text = True
            stt_service.stop_listening()
            print("\n⌨️ Switching to text input mode...")
            return
        
        query_lower = transcript.strip().lower()
        
        # Handle special commands
        if query_lower in ['quit', 'exit', 'stop', 'goodbye']:
            print("Goodbye!")
            stt_service.stop_listening()
            try:
                agent.cleanup()
            except Exception:
                pass
            import sys
            sys.exit(0)
        
        elif query_lower == 'clear conversation':
            agent.clear_conversation()
            print("Conversation history cleared!")
            print("🎤 Listening for your next command...")
            return
        
        elif query_lower == 'programs':
            print("Refreshing running programs...")
            programs = get_running_programs()
            agent.running_programs = programs
            display_running_programs(programs)
            print("🎤 Listening for your next command...")
            return
        
        elif 'stop speaking' in query_lower or 'be quiet' in query_lower:
            if agent.is_speaking():
                agent.stop_speaking()
                print("Stopped speaking.")
            else:
                print("Agent is not currently speaking.")
            print("🎤 Listening for your next command...")
            return
        
        # Decide how to handle the query based on task state
        with task_lock:
            is_running = task_running
        
        if is_running:
            # Task is running - pause, answer, resume
            print("⏸️  Pausing current task to answer your question...")
            mid_query_queue.put(transcript)
            agent.pause()
            
            # Process queued queries
            while not mid_query_queue.empty():
                q = mid_query_queue.get()
                answer_mid_query(q)
                mid_query_queue.task_done()
            
            # Auto-resume
            print("▶️  Resuming original task...")
            agent.resume()
        else:
            # No task running - start new task in background
            if task_thread and task_thread.is_alive():
                print("⚠️  Previous task still finishing up, please wait...")
                return
            
            task_thread = threading.Thread(target=run_task_async, args=(transcript,), daemon=True)
            task_thread.start()
    
    # Set the callback
    stt_service.on_transcription = on_transcription
    
    # Start listening
    print("\n🎤 Starting continuous listening...")
    if not stt_service.start_listening():
        print("ERROR: Failed to start listening!")
        return False
    
    print("🎤 Listening for your command...")
    
    # Keep listening until user switches to text mode
    try:
        while not switch_to_text:
            # Check if we're waiting for a command after trigger word detection
            if stt_service.is_waiting_for_command():
                print("\n🎤 Waiting for your command... (say 'yuki' to reset)")
                # Wait a bit longer when waiting for command
                time.sleep(1.0)
            else:
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\nSwitching to text input mode...")
        stt_service.stop_listening()
    
    # Wait for any running task to complete before switching modes
    if task_thread and task_thread.is_alive():
        print("⏳ Waiting for current task to complete...")
        task_thread.join(timeout=5.0)
    
    return True

def main():
    # Log session start
    agent_logger.log_session_start()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Yuki AI Agent with Voice Control')
    parser.add_argument('--voice', action='store_true', help='Start in voice control mode')
    parser.add_argument('--stt', action='store_true', help='Start in voice control mode (alias for --voice)')
    args = parser.parse_args()
    
    # Disable readline to prevent pyreadline3 issues on Windows
    try:
        import readline
        readline.set_history_length(0)
        readline.clear_history()
    except (ImportError, AttributeError):
        pass
    
    # Determine mode
    voice_mode = args.voice or args.stt
    
    if voice_mode:
        print("Yuki AI Agent - Voice Control Mode")
    else:
        print("Yuki AI Agent with Conversation Support")
    print("=" * 50)
    
    # Start overlay UI if available
    # if OVERLAY_AVAILABLE:
    #     try:
    #         print("Starting overlay UI...")
    #         start_overlay()
    #         print("Overlay UI started successfully!")
    #     except Exception as e:
    #         print(f"Failed to start overlay UI: {e}")
    #         print("Continuing without overlay...")
    
    # Overlay disabled
    print("Overlay UI disabled")
    
    # Check for running programs at startup
    print("Checking for running programs...")
    running_programs = get_running_programs()
    display_running_programs(running_programs)
    
    # Initialize agent with running programs context - using faster settings
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)  # Reduced temperature for faster, more focused responses
    
    # TTS configuration
    enable_tts = os.getenv("ENABLE_TTS", "false").lower() == "true"
    tts_voice_id = os.getenv("TTS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default ElevenLabs voice
    
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
    
    # Store running programs in agent for context
    agent.running_programs = running_programs
    
    
    # Pre-warm the system for faster first response
    print("Pre-warming system for faster response...")
    try:
        # Initialize desktop state cache
        agent.desktop.get_state(use_vision=False)
        print("System pre-warmed successfully!")
    except Exception as e:
        print(f"Pre-warming failed: {e}")
        print("System will still work, but first response may be slower.")
    
    # Show TTS status
    if enable_tts:
        from windows_use.agent.tts_service import is_tts_available
        tts_available = is_tts_available()
        print(f"TTS Status: {'Enabled' if tts_available else 'Disabled (API key not configured)'}")
    else:
        print("TTS Status: Disabled")
    
    # Check if STT is available
    stt_available = is_stt_available()
    
    print("\nCommands:")
    print("  - Type your query to interact with the agent")
    print("  - 💡 NEW: Tasks run in background - you can ask questions anytime!")
    print("  - Mid-task queries will pause, answer, then auto-resume")
    if stt_available:
        print("  - Type 'voice' or 'switch to voice' to enable voice control")
    print("  - Type 'clear' to clear conversation history")
    print("  - Type 'tts on/off' to enable/disable text-to-speech")
    print("  - Type 'stop speaking' to stop current speech")
    print("  - Type 'quit', 'exit', or 'q' to exit")
    print("  - Type 'help' to show this help message")
    print("  - Type 'programs' to refresh running programs list")
    print("=" * 50)
    
    # Start in voice mode if requested
    if voice_mode:
        run_voice_mode(agent)
    
    # Task execution state for text mode (same as voice mode)
    task_thread = None
    task_running = False
    task_lock = threading.Lock()
    mid_query_queue = queue.Queue()
    
    def run_task_async_text(task_query: str):
        """Run a task in background thread with pause support (text mode)"""
        nonlocal task_running
        try:
            with task_lock:
                task_running = True
            
            # Execute the agent task
            response = agent.invoke(task_query)
            
            # Handle response
            try:
                content = response.content or response.error or "No response"
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='replace')
                
                # Check if it's a question for user
                if "Human Tool" in str(response):
                    question = content.strip()
                    print(f"\n{question}")
                    
                    # Speak the question if TTS is enabled
                    if agent.tts_service and agent.tts_service.enabled:
                        agent.tts_service.speak_async(question)
                # Response is already printed by agent service
                
            except Exception:
                safe = (response.content or response.error or "No response")
                safe = safe.encode('ascii', errors='ignore').decode('ascii')
                print(f"\n{safe}")
                
        finally:
            # Mark task as finished and ensure agent is resumed
            agent.resume()
            with task_lock:
                task_running = False
            try:
                # Refresh desktop state to avoid stale UI after task actions
                agent.desktop.get_state(use_vision=False)
            except Exception:
                pass
            print()
            show_ready_indicator()
            sys.stdout.flush()
            sys.stderr.flush()
    
    def answer_mid_query_text(q: str):
        """Answer a user query conversationally without executing a new task (text mode)"""
        try:
            # Build a light conversational prompt using recent context
            context = agent.get_conversation_summary() if agent.enable_conversation else ""
            prompt = (
                f"You are in Chat mode. Answer the user's question briefly and conversationally. "
                f"Do not perform any actions or use tools - just provide information.\n\n"
                f"Context:\n{context}\n\nQuestion: {q}"
            )
            from langchain_core.messages import HumanMessage
            result = agent.llm.invoke([HumanMessage(content=prompt)])
            answer_text = getattr(result, 'content', None) or str(result)
            
            # Print the answer
            try:
                agent.console.print(Markdown(answer_text))
            except Exception:
                safe = answer_text.encode('ascii', errors='ignore').decode('ascii')
                print(safe)
                
        except Exception as e:
            answer_text = f"(Failed to answer: {e})"
            print(f"\n{answer_text}\n")
    
    while True:
        try:
            query = safe_input()
            
            if not query:
                continue
                
            # Handle special commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                # Clean up resources
                try:
                    agent.cleanup()
                except Exception:
                    pass
                # Stop overlay when exiting
                # if OVERLAY_AVAILABLE:
                #     try:
                #         stop_overlay()
                #     except Exception:
                #         pass
                # Log session end
                agent_logger.log_session_end()
                break
            elif query.lower() == 'clear':
                agent.clear_conversation()
                print("Conversation history cleared!")
                continue
            elif query.lower() == 'speed on':
                agent.desktop.cache_timeout = 1.0  # More aggressive caching
                print("Speed optimizations enabled!")
                continue
            elif query.lower() == 'speed off':
                agent.desktop.cache_timeout = 0.1  # Less caching
                agent.desktop.clear_cache()  # Clear existing cache
                print("Speed optimizations disabled!")
                continue
            elif query.lower() == 'help':
                print("\nYuki AI Agent Help")
                print("-" * 30)
                print("This agent can help you with Windows automation tasks like:")
                print("• Opening applications")
                print("• Clicking buttons and UI elements")
                print("• Typing text")
                print("• Scrolling and navigating")
                print("• Taking screenshots")
                print("• Running PowerShell commands")
                print("\n💡 Mid-Task Interruption:")
                print("• Tasks run in the background automatically")
                print("• You can ask questions anytime - even during task execution!")
                print("• Your question pauses the task, gets answered, then auto-resumes")
                print("• Example: While 'open 10 notepad windows' is running, ask 'what's the weather?'")
                print("\nThe agent remembers our conversation, so you can ask follow-up questions!")
                print("Try: 'Open notepad' then 'Type hello world'")
                print("\nMemory Commands:")
                print("• 'memories' - View all stored task solutions")
                print("• 'memory stats' - View memory statistics")
                print("• 'clear memories' - Clear all stored memories")
                print("\nTTS Commands:")
                print("• 'tts on' - Enable text-to-speech")
                print("• 'tts off' - Disable text-to-speech")
                print("• 'stop speaking' - Stop current speech")
                if is_stt_available():
                    print("\nVoice Control:")
                    print("• 'voice' or 'switch to voice' - Enable voice control mode")
                    print("• Say 'switch to text' when in voice mode to return to typing")
                    print("• Start with 'python main.py --voice' for voice-first mode")
                    print("• Voice mode also supports mid-task interruption!")
                print("\nSystem Commands:")
                print("• 'programs' - Refresh running programs list")
                continue
            elif query.lower() == 'programs':
                print("Refreshing running programs...")
                running_programs = get_running_programs()
                agent.running_programs = running_programs
                display_running_programs(running_programs)
                continue
            elif query.lower() == 'memories':
                memories = agent.list_memories()
                if memories:
                    print("\nStored Task Solutions:")
                    print("-" * 30)
                    for i, memory in enumerate(memories, 1):
                        print(f"{i}. Query: {memory['query']}")
                        print(f"   Successes: {memory['success_count']}")
                        print(f"   Last used: {memory['last_used']}")
                        print(f"   Tags: {', '.join(memory['tags']) if memory['tags'] else 'None'}")
                        print()
                else:
                    print("No memories stored yet. Complete some tasks to build memory!")
                continue
            elif query.lower() == 'memory stats':
                stats = agent.get_memory_stats()
                print(f"\nMemory Statistics:")
                print(f"Total memories: {stats['total_memories']}")
                print(f"Total successes: {stats['total_successes']}")
                if stats['total_memories'] > 0:
                    print(f"Average successes per memory: {stats['average_successes']:.1f}")
                continue
            elif query.lower() == 'clear memories':
                confirm = safe_input("Are you sure you want to clear all memories? (y/N): ").lower()
                if confirm == 'y':
                    agent.clear_memories()
                else:
                    print("Memory clear cancelled.")
                continue
            elif query.lower() == 'perf':
                agent.performance_monitor.print_stats()
                continue
            elif query.lower() == 'tts on':
                if agent.tts_service:
                    agent.tts_service.enabled = True
                    print("TTS enabled!")
                else:
                    print("TTS service not available. Check your ElevenLabs API key.")
                continue
            elif query.lower() == 'tts off':
                if agent.tts_service:
                    agent.tts_service.enabled = False
                    agent.stop_speaking()
                    print("TTS disabled!")
                else:
                    print("TTS service not available.")
                continue
            elif query.lower() in ['stop speaking', 'stop']:
                if agent.is_speaking():
                    agent.stop_speaking()
                    print("Stopped speaking.")
                else:
                    print("Agent is not currently speaking.")
                continue
            elif query.lower() in ['voice', 'switch to voice', 'voice mode', 'voice control']:
                if is_stt_available():
                    if run_voice_mode(agent):
                        # Returned from voice mode, continue text mode
                        print("\n⌨️ Text input mode resumed")
                        print("Ready for your next command...")
                    continue
                else:
                    print("Voice control not available. Please ensure:")
                    print("1. DEEPGRAM_API_KEY is set in .env")
                    print("2. deepgram-sdk is installed: pip install deepgram-sdk")
                    continue
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            # Clean up resources
            try:
                agent.cleanup()
            except Exception:
                pass
            # Stop overlay when interrupted
            # if OVERLAY_AVAILABLE:
            #     try:
            #         stop_overlay()
            #     except Exception:
            #         pass
            # Log session end
            agent_logger.log_session_end()
            break
        except Exception as input_error:
            print(f"\nInput system error: {input_error}")
            print("Attempting to recover...")
            try:
                # Try a simple input as last resort
                query = input("\nYou: ").strip()
                if not query:
                    continue
            except:
                print("Input system completely failed. Exiting...")
                break
        
        try:
            # Decide how to handle the query based on task state
            with task_lock:
                is_running = task_running
            
            if is_running:
                # Task is running - pause, answer, resume
                print("\n⏸️  Pausing current task to answer your question...")
                mid_query_queue.put(query)
                agent.pause()
                
                # Process queued queries
                while not mid_query_queue.empty():
                    q = mid_query_queue.get()
                    answer_mid_query_text(q)
                    mid_query_queue.task_done()
                
                # Auto-resume
                print("\n▶️  Resuming original task...\n")
                agent.resume()
                show_ready_indicator()
                sys.stdout.flush()
                sys.stderr.flush()
            else:
                # No task running - start new task in background
                print()  # Add spacing
                if task_thread and task_thread.is_alive():
                    print("⚠️  Previous task still finishing up, please wait...")
                    continue
                
                task_thread = threading.Thread(target=run_task_async_text, args=(query,), daemon=True)
                task_thread.start()
                print("🤖 Working on it in the background. You can type questions anytime.")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            # Stop overlay when interrupted
            # if OVERLAY_AVAILABLE:
            #     try:
            #         stop_overlay()
            #     except Exception:
            #         pass
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    main()