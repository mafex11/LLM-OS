"""
Speech-to-Text service using Deepgram for Windows-Use Agent
"""

import os
import tempfile
import threading
import time
import wave
from typing import Optional, Callable
import logging
from pathlib import Path

try:
    from deepgram import DeepgramClient
    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False
    print("Warning: Deepgram not available. Install with: pip install deepgram-sdk")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: PyAudio not available for microphone access. Install with: pip install pyaudio")

logger = logging.getLogger(__name__)

class STTService:
    """
    Speech-to-Text service using Deepgram with microphone input
    """
    
    def __init__(self, api_key: Optional[str] = None, enable_stt: bool = True):
        """
        Initialize STT service
        
        Args:
            api_key: Deepgram API key (if None, will try to get from env)
            enable_stt: Whether STT is enabled
        """
        self.enabled = enable_stt and DEEPGRAM_AVAILABLE and PYAUDIO_AVAILABLE
        self.is_recording = False
        self.audio_stream = None
        self.pyaudio_instance = None
        self.audio_frames = []
        
        if not self.enabled:
            logger.warning("STT is disabled or required dependencies not available")
            return
            
        # Initialize Deepgram
        api_key_to_use = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not api_key_to_use:
            logger.warning("No Deepgram API key provided. STT will be disabled.")
            self.enabled = False
            return
            
        self.deepgram = DeepgramClient(api_key=api_key_to_use)
        
        # Initialize PyAudio
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.audio_available = True
        except Exception as e:
            logger.warning(f"Failed to initialize PyAudio: {e}")
            self.audio_available = False
            self.enabled = False
            
        logger.info(f"STT Service initialized - Enabled: {self.enabled}, Audio: {self.audio_available}")
    
    def start_listening(self, on_transcript: Optional[Callable[[str], None]] = None, 
                       timeout: float = 5.0) -> str:
        """
        Start listening for speech and return transcribed text
        
        Args:
            on_transcript: Optional callback for real-time transcripts (not used in this implementation)
            timeout: Maximum time to listen (seconds)
            
        Returns:
            Final transcribed text
        """
        if not self.enabled:
            logger.warning("STT is not enabled")
            return ""
            
        if self.is_recording:
            logger.warning("Already recording")
            return ""
            
        try:
            # Record audio from microphone
            audio_file = self._record_audio(timeout)
            if not audio_file:
                return ""
            
            # Transcribe the recorded audio
            transcript = self.transcribe_audio_file(audio_file)
            
            # Clean up temporary file
            try:
                os.unlink(audio_file)
            except:
                pass
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error during speech recognition: {e}")
            return ""
    
    def _record_audio(self, duration: float) -> Optional[str]:
        """
        Record audio from microphone for specified duration
        
        Args:
            duration: Duration to record in seconds
            
        Returns:
            Path to recorded audio file or None if failed
        """
        if not self.enabled:
            return None
            
        try:
            # Audio configuration
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            
            # Calculate number of frames for the duration
            frames_to_record = int(RATE / CHUNK * duration)
            
            # Create temporary file for audio
            timestamp = int(time.time() * 1000)
            audio_filename = f"stt_audio_{timestamp}.wav"
            audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
            
            # Start audio stream
            self.audio_stream = self.pyaudio_instance.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            self.is_recording = True
            self.audio_frames = []
            
            logger.info(f"Recording audio for {duration} seconds...")
            
            # Record audio frames
            for i in range(frames_to_record):
                if not self.is_recording:
                    break
                data = self.audio_stream.read(CHUNK)
                self.audio_frames.append(data)
            
            # Stop recording
            self.stop_recording()
            
            # Save audio to file
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.pyaudio_instance.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(self.audio_frames))
            
            logger.info(f"Audio recorded successfully: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            self.stop_recording()
            return None
    
    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
            finally:
                self.audio_stream = None
    
    def transcribe_audio_file(self, audio_file_path: str) -> str:
        """
        Transcribe an audio file
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        if not self.enabled:
            logger.warning("STT is not enabled")
            return ""
            
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return ""
            
        try:
            with open(audio_file_path, "rb") as audio:
                buffer_data = audio.read()
                
            # Use the correct Deepgram API structure
            response = self.deepgram.listen.v1.media.transcribe_file(
                request=buffer_data,
                model="nova-2",
                language="en-US",
                smart_format=True,
                encoding="linear16"
            )
            
            if response.results and response.results.channels:
                transcript = response.results.channels[0].alternatives[0].transcript
                logger.info(f"File transcribed: {transcript}")
                return transcript
            else:
                logger.warning("No transcription results")
                return ""
                
        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            return ""
    
    def is_busy(self) -> bool:
        """Check if STT service is currently recording"""
        return self.is_recording
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_recording()
        
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
            finally:
                self.pyaudio_instance = None
    
    def __del__(self):
        """Destructor to clean up resources"""
        self.cleanup()

# Global STT service instance
_stt_service = None

def get_stt_service() -> STTService:
    """Get or create global STT service instance"""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service

def listen_for_speech(timeout: float = 5.0) -> str:
    """
    Convenience function to listen for speech using global STT service
    
    Args:
        timeout: Maximum time to listen (seconds)
        
    Returns:
        Transcribed text
    """
    stt = get_stt_service()
    return stt.start_listening(timeout=timeout)

def is_stt_available() -> bool:
    """Check if STT is available and configured"""
    stt = get_stt_service()
    return stt.enabled and stt.audio_available
