from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from dotenv import load_dotenv
from rich.markdown import Markdown
import os
import subprocess
import json
import time

# Import overlay functionality
try:
    from overlay_ui import start_overlay, stop_overlay
    OVERLAY_AVAILABLE = True
except ImportError:
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

def main():
    # Disable readline to prevent pyreadline3 issues on Windows
    try:
        import readline
        # Disable readline history and completion
        readline.set_history_length(0)
        readline.clear_history()
    except (ImportError, AttributeError):
        pass
    
    print("Windows-Use Agent with Conversation Support")
    print("=" * 50)
    
    # Start overlay UI if available
    if OVERLAY_AVAILABLE:
        try:
            print("Starting overlay UI...")
            start_overlay()
            print("Overlay UI started successfully!")
        except Exception as e:
            print(f"Failed to start overlay UI: {e}")
            print("Continuing without overlay...")
    
    # Check for running programs at startup
    print("Checking for running programs...")
    running_programs = get_running_programs()
    display_running_programs(running_programs)
    
    # Initialize agent with running programs context - using faster settings
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)  # Reduced temperature for faster, more focused responses
    
    # TTS configuration
    enable_tts = os.getenv("ENABLE_TTS", "true").lower() == "true"
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
    
    print("\nCommands:")
    print("  - Type your query to interact with the agent")
    print("  - Type 'clear' to clear conversation history")
    # print("  - Type 'loader on/off' to enable/disable visual loader")
    # print("  - Type 'speed on/off' to enable/disable speed optimizations")
    # print("  - Type 'perf' to show performance statistics")
    print("  - Type 'tts on/off' to enable/disable text-to-speech")
    print("  - Type 'stop speaking' to stop current speech")
    print("  - Type 'quit', 'exit', or 'q' to exit")
    print("  - Type 'help' to show this help message")
    print("  - Type 'programs' to refresh running programs list")
    print("=" * 50)
    
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
                if OVERLAY_AVAILABLE:
                    try:
                        stop_overlay()
                    except Exception:
                        pass
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
                print("\nWindows-Use Agent Help")
                print("-" * 30)
                print("This agent can help you with Windows automation tasks like:")
                print("• Opening applications")
                print("• Clicking buttons and UI elements")
                print("• Typing text")
                print("• Scrolling and navigating")
                print("• Taking screenshots")
                print("• Running PowerShell commands")
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
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            # Clean up resources
            try:
                agent.cleanup()
            except Exception:
                pass
            # Stop overlay when interrupted
            if OVERLAY_AVAILABLE:
                try:
                    stop_overlay()
                except Exception:
                    pass
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
            # Process the query
            print()  # Add spacing
            response = agent.invoke(query)
            
            # Check if the agent is asking a question
            if response.content and "USER QUESTION:" in response.content:
                print(f"\nAgent: {response.content}")
                # Get user response and continue the conversation
                user_response = safe_input("\nYour answer: ")
                if user_response:
                    # Continue the conversation with the user's response
                    print()  # Add spacing
                    agent.print_response(user_response)
                else:
                    print("No response provided. Continuing...")
            else:
                # Normal response - handle encoding safely
                try:
                    content = response.content or response.error or "No response"
                    # Ensure content is properly encoded
                    if isinstance(content, bytes):
                        content = content.decode('utf-8', errors='replace')
                    agent.console.print(Markdown(content))
                except UnicodeEncodeError as ue:
                    # Fallback: remove problematic characters
                    safe_content = content.encode('ascii', errors='ignore').decode('ascii')
                    print(f"\n{safe_content}")
                    print(f"\n(Note: Some special characters were removed due to console encoding limitations)")
            
            # Ensure we always return to the input prompt
            print()  # Add spacing before next input
            
            # Show ready indicator
            show_ready_indicator()
            
            # Force flush to ensure output is displayed
            import sys
            sys.stdout.flush()
            sys.stderr.flush()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            # Stop overlay when interrupted
            if OVERLAY_AVAILABLE:
                try:
                    stop_overlay()
                except Exception:
                    pass
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    main()