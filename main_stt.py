from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from windows_use.agent import Agent
from windows_use.agent.stt_service import STTService
from windows_use.agent.logger import agent_logger
from dotenv import load_dotenv
from rich.markdown import Markdown
import os
import subprocess
import json
import time

load_dotenv()

# Fix Windows console encoding issues
import sys
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleOutputCP(65001)
    except:
        pass
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def get_running_programs():
    """Get list of currently running programs using PowerShell"""
    try:
        cmd = [
            "powershell", "-Command",
            "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object ProcessName, MainWindowTitle, Id | ConvertTo-Json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            processes = json.loads(result.stdout)
            if isinstance(processes, dict):
                processes = [processes]
            
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
    # Log session start
    agent_logger.log_session_start()
    
    print("Windows-Use Agent with Deepgram STT")
    print("=" * 50)
    
    # Check for running programs at startup
    print("Checking for running programs...")
    running_programs = get_running_programs()
    display_running_programs(running_programs)
    
    # Initialize agent
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
    
    # TTS configuration
    enable_tts = os.getenv("ENABLE_TTS", "false").lower() == "true"
    tts_voice_id = os.getenv("TTS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    
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
    
    # Pre-warm the system
    print("Pre-warming system for faster response...")
    try:
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
    
    # Initialize STT service
    print("\nInitializing Deepgram STT...")
    stt_service = STTService(enable_stt=True)
    
    if not stt_service.enabled:
        print("ERROR: Deepgram STT is not available!")
        print("Please ensure:")
        print("1. DEEPGRAM_API_KEY is set in your .env file")
        print("2. deepgram-sdk is installed: pip install deepgram-sdk")
        return
    
    print("STT Status: Enabled and ready")
    print("\nVoice Commands:")
    print("  - Speak your query naturally")
    print("  - Say 'clear conversation' to clear history")
    print("  - Say 'quit' or 'exit' to exit")
    print("  - Say 'programs' to refresh running programs list")
    print("=" * 50)
    
    # Flag to track if we're waiting for next query
    waiting_for_query = True
    
    def on_transcription(transcript: str):
        """Callback when transcription is received"""
        nonlocal waiting_for_query
        
        if not waiting_for_query:
            print(f"\n[Ignoring speech while processing: '{transcript}']")
            return
        
        print(f"\n🎤 You said: {transcript}")
        
        # Log STT input
        agent_logger.log_stt(transcript)
        
        # Mark that we're processing
        waiting_for_query = False
        
        # Process the query
        process_query(transcript)
        
        # Mark that we're ready for next query
        waiting_for_query = True
        print("\n🎤 Listening for your next command...")
    
    def process_query(query: str):
        """Process a voice query through the agent"""
        query = query.strip().lower()
        
        # Handle special commands
        if query in ['quit', 'exit', 'stop', 'goodbye']:
            print("Goodbye!")
            stt_service.stop_listening()
            try:
                agent.cleanup()
            except Exception:
                pass
            # Log session end
            agent_logger.log_session_end()
            sys.exit(0)
        
        elif query == 'clear conversation':
            agent.clear_conversation()
            print("Conversation history cleared!")
            return
        
        elif query == 'programs':
            print("Refreshing running programs...")
            programs = get_running_programs()
            agent.running_programs = programs
            display_running_programs(programs)
            return
        
        elif 'stop speaking' in query or 'be quiet' in query:
            if agent.is_speaking():
                agent.stop_speaking()
                print("Stopped speaking.")
            else:
                print("Agent is not currently speaking.")
            return
        
        # Process the query through agent
        try:
            print()
            response = agent.invoke(query)
            
            # Handle response
            if response.content and "Human Tool" in str(response):
                # Extract and display the question
                question = response.content.strip()
                print(f"\n{question}")
                
                # Speak the question if TTS is enabled
                if agent.tts_service and agent.tts_service.enabled:
                    agent.tts_service.speak_async(question)
                
                # For questions, we'll wait for voice response
                print("\n🎤 Listening for your answer...")
            else:
                # Response is already printed by the agent service
                pass
            
            print()
            sys.stdout.flush()
            sys.stderr.flush()
            
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.")
    
    # Set the callback
    stt_service.on_transcription = on_transcription
    
    # Start listening
    print("\n🎤 Starting continuous listening...")
    if not stt_service.start_listening():
        print("ERROR: Failed to start listening!")
        return
    
    print("🎤 Listening for your command...")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        stt_service.stop_listening()
        try:
            agent.cleanup()
        except Exception:
            pass
        # Log session end
        agent_logger.log_session_end()

if __name__ == "__main__":
    main()

