from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
# from langchain_groq import ChatGroq
from windows_use.agent import Agent
from dotenv import load_dotenv
from rich.markdown import Markdown
import os
import subprocess
import json
import time
# from windows_use.agent.ollama_client import OllamaChat

load_dotenv()

# Disable readline to prevent pyreadline3 access violation issues on Windows
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

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
    
    # Check for running programs at startup
    print("Checking for running programs...")
    running_programs = get_running_programs()
    display_running_programs(running_programs)
    
    # Initialize agent with running programs context - using faster settings
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)  # Reduced temperature for faster, more focused responses
    agent = Agent(llm=llm, browser='chrome', use_vision=False, enable_conversation=True, literal_mode=True, max_steps=15)  # Reduced max_steps from 20 to 15
    
    # Store running programs in agent for context
    agent.running_programs = running_programs
    
    # Enable loader by default (can be disabled with 'loader off' command)
    agent.set_loader_enabled(True)
    
    # Pre-warm the system for faster first response
    print("Pre-warming system for faster response...")
    try:
        # Initialize desktop state cache
        agent.desktop.get_state(use_vision=False)
        print("System pre-warmed successfully!")
    except Exception as e:
        print(f"Pre-warming failed: {e}")
        print("System will still work, but first response may be slower.")
    
    print("\nCommands:")
    print("  - Type your query to interact with the agent")
    print("  - Type 'voice' to enable voice input mode")
    print("  - Type 'clear' to clear conversation history")
    print("  - Type 'loader on/off' to enable/disable visual loader")
    print("  - Type 'speed on/off' to enable/disable speed optimizations")
    print("  - Type 'perf' to show performance statistics")
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
                break
            elif query.lower() == 'clear':
                agent.clear_conversation()
                print("Conversation history cleared!")
                continue
            elif query.lower() == 'loader on':
                agent.set_loader_enabled(True)
                print("Visual loader enabled!")
                continue
            elif query.lower() == 'loader off':
                agent.set_loader_enabled(False)
                print("Visual loader disabled!")
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
                print("• Voice commands and responses")
                print("\nThe agent remembers our conversation, so you can ask follow-up questions!")
                print("Try: 'Open notepad' then 'Type hello world'")
                print("\nVoice Commands:")
                print("• 'voice' - Enter voice input mode")
                print("  - Wake word mode: Say 'hey windows use' to activate")
                print("  - Push-to-talk: Press Enter to start/stop speaking")
                print("  - Continuous: Always listening for commands")
                print("  - Test voice output")
                print("\nMemory Commands:")
                print("• 'memories' - View all stored task solutions")
                print("• 'memory stats' - View memory statistics")
                print("• 'clear memories' - Clear all stored memories")
                print("\nSystem Commands:")
                print("• 'programs' - Refresh running programs list")
                print("• 'loader on/off' - Enable/disable visual loader overlay")
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
            elif query.lower() == 'voice':
                print("\nVoice Input Mode")
                print("-" * 30)
                print("Choose voice input mode:")
                print("1. Wake word mode (say 'hey windows use' to activate)")
                print("2. Push-to-talk mode (press Enter to start/stop)")
                print("3. Continuous mode (always listening)")
                print("4. Test voice output")
                print("5. Back to text mode")
                
                choice = safe_input("\nEnter choice (1-5): ")
                
                if choice == '1':
                    print("\nWake word mode activated!")
                    print("Say 'hey windows use' followed by your command")
                    print("Example: 'hey windows use, open notepad'")
                    print("Press Ctrl+C to stop voice mode")
                    
                    try:
                        from windows_use.agent.voice.service import VoiceService
                        voice_service = VoiceService(wake_word="hey windows use", voice_mode="wake_word", model="base")
                        
                        if not voice_service.is_available():
                            print("Voice service not available. Please check audio devices.")
                            continue
                        
                        # Start continuous wake word listening
                        transcription_result = None
                        
                        def on_transcription(text: str):
                            nonlocal transcription_result
                            print(f"\nCommand: {text}")
                            # Process the command through the agent
                            response = agent.invoke(text)
                            agent.console.print(Markdown(response.content or response.error))
                            
                            # Automatically convert response to speech
                            if response.content:
                                try:
                                    voice_service.speak(response.content)
                                except Exception as e:
                                    print(f"TTS Error: {e}")
                            
                            print("\nListening for next command...")
                        
                        def on_wake_word():
                            print("Wake word detected! Listening for command...")
                        
                        voice_service.start_listening(
                            duration=300,  # 5 minutes
                            on_transcription=on_transcription,
                            on_wake_word=on_wake_word
                        )
                        
                        # Keep listening until interrupted
                        while True:
                            time.sleep(1)
                            
                    except KeyboardInterrupt:
                        print("\nVoice mode stopped.")
                        if 'voice_service' in locals():
                            voice_service.stop_listening()
                    except ImportError:
                        print("Voice functionality not available. Please install RealtimeSTT and audio dependencies.")
                    except Exception as e:
                        print(f"Voice error: {e}")
                    continue
                    
                elif choice == '2':
                    print("\nPush-to-talk mode activated!")
                    print("Press Enter to start speaking, then Enter again to stop")
                    print("Press Ctrl+C to exit voice mode")
                    
                    try:
                        from windows_use.agent.voice.service import VoiceService
                        voice_service = VoiceService(voice_mode="push_to_talk", model="base")
                        
                        if not voice_service.is_available():
                            print("Voice service not available. Please check audio devices.")
                            continue
                        
                        while True:
                            safe_input("\nPress Enter to start speaking...")
                            print("Listening... (Press Enter to stop)")
                            
                            transcription_result = None
                            
                            def on_transcription(text: str):
                                nonlocal transcription_result
                                transcription_result = text
                            
                            voice_service.start_listening(
                                duration=30,  # 30 seconds max
                                on_transcription=on_transcription
                            )
                            
                            # Wait for Enter to stop or timeout
                            import threading
                            stop_listening = False
                            
                            def wait_for_enter():
                                nonlocal stop_listening
                                input()
                                stop_listening = True
                                voice_service.stop_listening()
                            
                            enter_thread = threading.Thread(target=wait_for_enter, daemon=True)
                            enter_thread.start()
                            
                            # Wait for transcription or stop signal
                            start_time = time.time()
                            while not stop_listening and time.time() - start_time < 30:
                                if transcription_result:
                                    break
                                time.sleep(0.1)
                            
                            voice_service.stop_listening()
                            
                            if transcription_result:
                                print(f"\nCommand: {transcription_result}")
                                response = agent.invoke(transcription_result)
                                agent.console.print(Markdown(response.content or response.error))
                                
                                # Automatically convert response to speech
                                if response.content:
                                    try:
                                        voice_service.speak(response.content)
                                    except Exception as e:
                                        print(f"TTS Error: {e}")
                            else:
                                print("No command detected.")
                                
                    except KeyboardInterrupt:
                        print("\nVoice mode stopped.")
                    except ImportError:
                        print("Voice functionality not available. Please install RealtimeSTT and audio dependencies.")
                    except Exception as e:
                        print(f"Voice error: {e}")
                    continue
                    
                elif choice == '3':
                    print("\nContinuous mode activated!")
                    print("Always listening for commands...")
                    print("Press Ctrl+C to stop voice mode")
                    
                    try:
                        from windows_use.agent.voice.service import VoiceService
                        voice_service = VoiceService(voice_mode="continuous", model="base")
                        
                        if not voice_service.is_available():
                            print("Voice service not available. Please check audio devices.")
                            continue
                        
                        def on_transcription(text: str):
                            print(f"\nCommand: {text}")
                            response = agent.invoke(text)
                            agent.console.print(Markdown(response.content or response.error))
                            
                            # Automatically convert response to speech
                            if response.content:
                                try:
                                    voice_service.speak(response.content)
                                except Exception as e:
                                    print(f"TTS Error: {e}")
                            
                            print("\nListening for next command...")
                        
                        voice_service.start_listening(
                            duration=300,  # 5 minutes
                            on_transcription=on_transcription
                        )
                        
                        # Keep listening until interrupted
                        while True:
                            time.sleep(1)
                            
                    except KeyboardInterrupt:
                        print("\nVoice mode stopped.")
                        if 'voice_service' in locals():
                            voice_service.stop_listening()
                    except ImportError:
                        print("Voice functionality not available. Please install RealtimeSTT and audio dependencies.")
                    except Exception as e:
                        print(f"Voice error: {e}")
                    continue
                    
                elif choice == '4':
                    print("\nTesting voice output...")
                    test_text = safe_input("Enter text to speak: ")
                    if test_text:
                        try:
                            from windows_use.agent.voice.service import VoiceService
                            voice_service = VoiceService()
                            voice_service.speak(test_text)
                        except ImportError:
                            print("Voice functionality not available. Please install TTS dependencies.")
                        except Exception as e:
                            print(f"Voice error: {e}")
                    continue
                    
                elif choice == '5':
                    print("Returning to text mode...")
                    continue
                else:
                    print("Invalid choice. Returning to main menu.")
                    continue
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
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
                # Normal response
                agent.console.print(Markdown(response.content or response.error))
            
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
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    main()