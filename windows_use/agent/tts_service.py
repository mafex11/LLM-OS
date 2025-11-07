"""
Text-to-Speech service using ElevenLabs for Yuki AI Agent
"""

import os
import tempfile
import threading
import time
from typing import Optional, Callable
import logging
from pathlib import Path

try:
    from elevenlabs import ElevenLabs, Voice, VoiceSettings, save
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("Warning: ElevenLabs not available. Install with: pip install elevenlabs")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: Pygame not available for audio playback. Install with: pip install pygame")

logger = logging.getLogger(__name__)

class TTSService:
    """
    Text-to-Speech service using ElevenLabs with audio playback capabilities
    """
    
    def __init__(self, api_key: Optional[str] = None, voice_id: str = "21m00Tcm4TlvDq8ikWAM", 
                 model_id: str = "eleven_turbo_v2", enable_tts: bool = True):
        """
        Initialize TTS service
        
        Args:
            api_key: ElevenLabs API key (if None, will try to get from env)
            voice_id: Voice ID to use for TTS
            model_id: ElevenLabs model ID
            enable_tts: Whether TTS is enabled
        """
        self.enabled = enable_tts and ELEVENLABS_AVAILABLE
        self.voice_id = voice_id
        self.model_id = model_id
        self.is_speaking = False
        self.current_audio_file = None
        self.audio_queue = []
        self.playback_thread = None
        self.stop_playback = threading.Event()
        
        if not self.enabled:
            logger.warning("TTS is disabled or ElevenLabs not available")
            return
            
        # Initialize ElevenLabs
        api_key_to_use = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not api_key_to_use:
            logger.warning("No ElevenLabs API key provided. TTS will be disabled.")
            self.enabled = False
            return
            
        self.client = ElevenLabs(api_key=api_key_to_use)
        
        # Initialize pygame for audio playback
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self.audio_available = True
            except Exception as e:
                logger.warning(f"Failed to initialize pygame mixer: {e}")
                self.audio_available = False
        else:
            self.audio_available = False
            
        logger.info(f"TTS Service initialized - Enabled: {self.enabled}, Audio: {self.audio_available}")
    
    def generate_speech(self, text: str) -> Optional[str]:
        """
        Generate speech audio from text
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Path to generated audio file or None if failed
        """
        if not self.enabled:
            return None
            
        if not text or not text.strip():
            return None
            
        try:
            # Clean up previous audio file
            if self.current_audio_file and os.path.exists(self.current_audio_file):
                try:
                    os.unlink(self.current_audio_file)
                except:
                    pass
            
            # Generate unique filename
            timestamp = int(time.time() * 1000)
            audio_filename = f"tts_audio_{timestamp}.mp3"
            audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
            
            logger.debug(f"Generating speech for: {text[:50]}...")
            
            # Generate audio using ElevenLabs
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.5,
                    style=0.0,
                    use_speaker_boost=True
                )
            )
            
            # Save audio to file
            save(audio, audio_path)
            
            self.current_audio_file = audio_path
            logger.debug(f"Speech generated successfully: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            return None
    
    def play_audio(self, audio_path: str, blocking: bool = True) -> bool:
        """
        Play audio file using pygame
        
        Args:
            audio_path: Path to audio file
            blocking: Whether to block until playback is complete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.audio_available or not os.path.exists(audio_path):
            return False
            
        try:
            self.is_speaking = True
            self.stop_playback.clear()
            
            if blocking:
                # Play audio synchronously
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy() and not self.stop_playback.is_set():
                    time.sleep(0.1)
                    
                self.is_speaking = False
                return True
            else:
                # Play audio asynchronously
                def play_async():
                    try:
                        pygame.mixer.music.load(audio_path)
                        pygame.mixer.music.play()
                        
                        while pygame.mixer.music.get_busy() and not self.stop_playback.is_set():
                            time.sleep(0.1)
                            
                    except Exception as e:
                        logger.error(f"Error during async playback: {e}")
                    finally:
                        self.is_speaking = False
                
                self.playback_thread = threading.Thread(target=play_async, daemon=True)
                self.playback_thread.start()
                return True
                
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            self.is_speaking = False
            return False
    
    def speak(self, text: str, blocking: bool = False) -> bool:
        """
        Generate and play speech from text
        
        Args:
            text: Text to speak
            blocking: Whether to block until speech is complete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("TTS is disabled")
            return False
            
        if not text or not text.strip():
            return False
            
        # Stop any current speech
        self.stop_current_speech()
        
        # Generate audio
        audio_path = self.generate_speech(text)
        if not audio_path:
            return False
            
        # Play audio
        return self.play_audio(audio_path, blocking=blocking)
    
    def stop_current_speech(self):
        """Stop current speech playback"""
        if self.is_speaking:
            self.stop_playback.set()
            if PYGAME_AVAILABLE and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            self.is_speaking = False
            
        # Wait for playback thread to finish
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)
    
    def speak_async(self, text: str) -> bool:
        """
        Speak text asynchronously (non-blocking)
        
        Args:
            text: Text to speak
            
        Returns:
            True if speech started successfully, False otherwise
        """
        return self.speak(text, blocking=False)
    
    def speak_sync(self, text: str) -> bool:
        """
        Speak text synchronously (blocking)
        
        Args:
            text: Text to speak
            
        Returns:
            True if speech completed successfully, False otherwise
        """
        return self.speak(text, blocking=True)
    
    def is_busy(self) -> bool:
        """Check if TTS service is currently speaking"""
        return self.is_speaking
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_current_speech()
        
        # Clean up audio files
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                os.unlink(self.current_audio_file)
            except:
                pass
                
        # Clean up pygame
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.quit()
            except:
                pass
    
    def __del__(self):
        """Destructor to clean up resources"""
        self.cleanup()

# Global TTS service instance
_tts_service = None

def get_tts_service() -> TTSService:
    """Get or create global TTS service instance"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service

def speak_text(text: str, blocking: bool = False) -> bool:
    """
    Convenience function to speak text using global TTS service
    
    Args:
        text: Text to speak
        blocking: Whether to block until speech is complete
        
    Returns:
        True if successful, False otherwise
    """
    tts = get_tts_service()
    return tts.speak(text, blocking=blocking)

def is_tts_available() -> bool:
    """Check if TTS is available and configured"""
    tts = get_tts_service()
    return tts.enabled and tts.audio_available
