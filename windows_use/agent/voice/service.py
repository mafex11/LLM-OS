"""
Voice service module for Windows-Use agent.
Handles Speech-to-Text (STT) and Text-to-Speech (TTS) functionality.
"""

import threading
import time
from typing import Callable, Optional, Literal
from RealtimeSTT import AudioToTextRecorder
import pyttsx3
from rich.console import Console
from termcolor import colored
import logging

logger = logging.getLogger(__name__)
console = Console()

class VoiceService:
    """
    Voice service for handling STT and TTS operations.
    Integrates RealtimeSTT for speech recognition and pyttsx3 for text-to-speech.
    """
    
    def __init__(self, 
                 wake_word: str = "hey windows use",
                 language: str = "en",
                 model: str = "base",
                 voice_mode: Literal['push_to_talk', 'continuous', 'wake_word'] = 'wake_word'):
        self.wake_word = wake_word
        self.language = language
        self.model = model
        self.voice_mode = voice_mode
        self.is_listening = False
        self.is_voice_enabled = True
        self.recorder = None
        self.tts_engine = None
        self.transcription_callback = None
        self.wake_word_callback = None
        self._setup_tts()
        
    def _setup_tts(self):
        """Initialize the text-to-speech engine."""
        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Set a default voice (usually the first available)
                self.tts_engine.setProperty('voice', voices[0].id)
            self.tts_engine.setProperty('rate', 200)  # Speed of speech
            self.tts_engine.setProperty('volume', 0.9)  # Volume level
            logger.info("TTS engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.tts_engine = None
    
    def speak(self, text: str, voice: Literal['default', 'male', 'female'] = 'default', rate: int = 200):
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to convert to speech
            voice: Voice type ('default', 'male', 'female')
            rate: Speech rate in words per minute
        """
        if not self.tts_engine:
            console.print("[red]TTS engine not available[/red]")
            return False
            
        try:
            # Set voice properties
            self.tts_engine.setProperty('rate', rate)
            
            # Try to set voice type if available
            if self.tts_engine.getProperty('voices'):
                voices = self.tts_engine.getProperty('voices')
                if voice == 'male' and len(voices) > 1:
                    # Try to find a male voice (usually lower index)
                    for v in voices:
                        if 'male' in v.name.lower() or 'man' in v.name.lower():
                            self.tts_engine.setProperty('voice', v.id)
                            break
                elif voice == 'female' and len(voices) > 1:
                    # Try to find a female voice (usually higher index)
                    for v in voices:
                        if 'female' in v.name.lower() or 'woman' in v.name.lower():
                            self.tts_engine.setProperty('voice', v.id)
                            break
            
            # Speak the text
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            logger.info(f"Spoke: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            console.print(f"[red]TTS Error: {e}[/red]")
            return False
    
    def start_listening(self, 
                       duration: int = 10,
                       on_transcription: Optional[Callable[[str], None]] = None,
                       on_wake_word: Optional[Callable[[], None]] = None):
        """
        Start listening for voice input using RealtimeSTT.
        
        Args:
            duration: Maximum duration to listen in seconds
            on_transcription: Callback function for transcription updates
            on_wake_word: Callback function for wake word detection
        """
        if self.is_listening:
            console.print("[yellow]Already listening for voice input[/yellow]")
            return False
            
        self.transcription_callback = on_transcription
        self.wake_word_callback = on_wake_word
        
        try:
            # Configure RealtimeSTT based on voice mode
            if self.voice_mode == 'wake_word':
                self.recorder = AudioToTextRecorder(
                    model=self.model,
                    language=self.language,
                    wake_words=self.wake_word,
                    wake_words_sensitivity=0.6,
                    wake_word_activation_delay=0,
                    wake_word_timeout=duration,
                    silero_sensitivity=0.6,
                    post_speech_silence_duration=0.2,
                    min_length_of_recording=1.0,
                    on_realtime_transcription_update=self._on_transcription_update,
                    on_wakeword_detected=self._on_wake_word_detected,
                    on_wakeword_timeout=self._on_wake_word_timeout
                )
            elif self.voice_mode == 'continuous':
                self.recorder = AudioToTextRecorder(
                    model=self.model,
                    language=self.language,
                    silero_sensitivity=0.6,
                    post_speech_silence_duration=0.2,
                    min_length_of_recording=1.0,
                    on_realtime_transcription_update=self._on_transcription_update
                )
            else:  # push_to_talk
                self.recorder = AudioToTextRecorder(
                    model=self.model,
                    language=self.language,
                    silero_sensitivity=0.6,
                    post_speech_silence_duration=0.2,
                    min_length_of_recording=1.0,
                    on_realtime_transcription_update=self._on_transcription_update
                )
            
            self.is_listening = True
            console.print(f"[green]Listening for voice input... (Mode: {self.voice_mode})[/green]")
            if self.voice_mode == 'wake_word':
                console.print(f"[cyan]Say '{self.wake_word}' to activate[/cyan]")
            
            # Start listening in a separate thread
            self._listen_thread = threading.Thread(target=self._listen_worker, daemon=True)
            self._listen_thread.start()
            return True
            
        except Exception as e:
            logger.error(f"Failed to start voice listening: {e}")
            console.print(f"[red]Voice listening error: {e}[/red]")
            return False
    
    def stop_listening(self):
        """Stop listening for voice input."""
        if not self.is_listening:
            return
            
        self.is_listening = False
        if self.recorder:
            try:
                self.recorder.stop()
            except:
                pass
        console.print("[yellow]Stopped listening for voice input[/yellow]")
    
    def _listen_worker(self):
        """Worker thread for voice listening."""
        try:
            with self.recorder as recorder:
                while self.is_listening:
                    text = recorder.text()
                    if text and text.strip():
                        self._on_transcription_update(text.strip())
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"Voice listening worker error: {e}")
        finally:
            self.is_listening = False
    
    def _on_transcription_update(self, text: str):
        """Handle real-time transcription updates."""
        if text and text.strip():
            console.print(f"[blue]Heard: {text}[/blue]")
            if self.transcription_callback:
                self.transcription_callback(text)
    
    def _on_wake_word_detected(self):
        """Handle wake word detection."""
        console.print(f"[green]Wake word '{self.wake_word}' detected![/green]")
        if self.wake_word_callback:
            self.wake_word_callback()
    
    def _on_wake_word_timeout(self):
        """Handle wake word timeout."""
        console.print("[yellow]Wake word timeout - stopping listening[/yellow]")
        self.stop_listening()
    
    def set_voice_mode(self, mode: Literal['push_to_talk', 'continuous', 'wake_word']):
        """Change the voice input mode."""
        if self.is_listening:
            self.stop_listening()
        self.voice_mode = mode
        console.print(f"[cyan]Voice mode changed to: {mode}[/cyan]")
    
    def set_wake_word(self, wake_word: str):
        """Change the wake word."""
        self.wake_word = wake_word
        console.print(f"[cyan]Wake word changed to: '{wake_word}'[/cyan]")
    
    def toggle_voice(self):
        """Toggle voice functionality on/off."""
        self.is_voice_enabled = not self.is_voice_enabled
        status = "enabled" if self.is_voice_enabled else "disabled"
        console.print(f"[cyan]Voice functionality {status}[/cyan]")
        return self.is_voice_enabled
    
    def is_available(self) -> bool:
        """Check if voice functionality is available."""
        return self.tts_engine is not None and self.is_voice_enabled
