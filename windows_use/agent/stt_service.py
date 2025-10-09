"""
Speech-to-Text service using Deepgram for Windows-Use Agent
Provides continuous listening with automatic wake detection
"""

import os
import threading
import queue
import time
from typing import Optional, Callable
import logging
from pathlib import Path

try:
    from deepgram import (
        DeepgramClient,
        DeepgramClientOptions,
        LiveTranscriptionEvents,
        LiveOptions,
        Microphone,
    )
    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False
    print("Warning: Deepgram not available. Install with: pip install deepgram-sdk")

logger = logging.getLogger(__name__)

class STTService:
    """
    Speech-to-Text service using Deepgram with continuous listening
    """
    
    def __init__(self, api_key: Optional[str] = None, enable_stt: bool = True, 
                 on_transcription: Optional[Callable[[str], None]] = None,
                 latency_mode: str = "fast"):
        """
        Initialize STT service
        
        Args:
            api_key: Deepgram API key (if None, will try to get from env)
            enable_stt: Whether STT is enabled
            on_transcription: Callback function when transcription is received
            latency_mode: 'ultra' (100-200ms), 'fast' (300-500ms), or 'balanced' (800-1500ms, default)
        """
        self.enabled = enable_stt and DEEPGRAM_AVAILABLE
        self.is_listening = False
        self.transcription_queue = queue.Queue()
        self.on_transcription = on_transcription
        self.stop_event = threading.Event()
        self.listening_thread = None
        self.deepgram_connection = None
        self.microphone = None
        self.latency_mode = latency_mode.lower()
        
        # Configure latency settings based on mode
        if self.latency_mode == "ultra":
            self.silence_threshold = 0.2  # 200ms
            self.utterance_end_ms = "300"  # 300ms
            self.endpointing = 100  # 100ms
            self.poll_interval = 0.02  # 20ms
        elif self.latency_mode == "fast":
            self.silence_threshold = 0.5  # 500ms
            self.utterance_end_ms = "1000"  # 1000ms
            self.endpointing = 100  # 150ms
            self.poll_interval = 0.05 # 50ms
        else:  # balanced
            self.silence_threshold = 1.5  # 1.5s
            self.utterance_end_ms = "1000"  # 1s
            self.endpointing = 300  # 300ms
            self.poll_interval = 0.1  # 100ms
        
        if not self.enabled:
            logger.warning("STT is disabled or Deepgram not available")
            return
            
        # Get API key
        api_key_to_use = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not api_key_to_use:
            logger.warning("No Deepgram API key provided. STT will be disabled.")
            self.enabled = False
            return
        
        # Initialize Deepgram client
        try:
            config = DeepgramClientOptions(
                options={"keepalive": "true"}
            )
            self.deepgram = DeepgramClient(api_key_to_use, config)
            logger.info(f"Deepgram STT Service initialized successfully (latency_mode={self.latency_mode}, silence_threshold={self.silence_threshold}s)")
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram client: {e}")
            self.enabled = False
    
    def start_listening(self) -> bool:
        """
        Start continuous listening for speech
        
        Returns:
            True if listening started successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("STT is disabled")
            return False
        
        if self.is_listening:
            logger.warning("Already listening")
            return True
        
        try:
            # Reset stop event
            self.stop_event.clear()
            
            # Start listening thread
            self.listening_thread = threading.Thread(
                target=self._listen_loop,
                daemon=True
            )
            self.listening_thread.start()
            
            logger.info("Started listening for speech...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start listening: {e}")
            return False
    
    def _listen_loop(self):
        """Main listening loop that handles Deepgram streaming"""
        try:
            # Create a websocket connection to Deepgram
            self.deepgram_connection = self.deepgram.listen.websocket.v("1")
            
            # Buffer to accumulate partial transcripts
            self.current_transcript = ""
            self.last_speech_time = time.time()
            
            # Capture service instance for event handlers
            service = self
            
            def on_message(dg_self, result, **kwargs):
                """Handle incoming transcription results"""
                try:
                    sentence = result.channel.alternatives[0].transcript
                    
                    if len(sentence) == 0:
                        return
                    
                    # Check if this is a final result
                    if result.is_final:
                        # Accumulate the transcript
                        service.current_transcript += " " + sentence
                        service.current_transcript = service.current_transcript.strip()
                        service.last_speech_time = time.time()
                        
                        logger.info(f"Final transcript: {sentence}")
                        
                        # Check for silence to finalize
                        service._check_and_finalize_transcript()
                    else:
                        # Interim result
                        logger.debug(f"Interim: {sentence}")
                        
                except Exception as e:
                    logger.error(f"Error in on_message: {e}")
            
            def on_metadata(dg_self, metadata, **kwargs):
                """Handle metadata"""
                logger.debug(f"Metadata: {metadata}")
            
            def on_speech_started(dg_self, speech_started, **kwargs):
                """Handle speech started event"""
                logger.debug("Speech started")
                service.current_transcript = ""
                service.last_speech_time = time.time()
            
            def on_utterance_end(dg_self, utterance_end, **kwargs):
                """Handle utterance end event"""
                logger.debug("Utterance end")
                service._finalize_transcript()
            
            def on_error(dg_self, error, **kwargs):
                """Handle errors"""
                logger.error(f"Deepgram error: {error}")
            
            def on_close(dg_self, close, **kwargs):
                """Handle connection close"""
                logger.info("Deepgram connection closed")
            
            # Register event handlers
            self.deepgram_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.deepgram_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
            self.deepgram_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
            self.deepgram_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
            self.deepgram_connection.on(LiveTranscriptionEvents.Error, on_error)
            self.deepgram_connection.on(LiveTranscriptionEvents.Close, on_close)
            
            # Configure Deepgram options based on latency mode
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                utterance_end_ms=self.utterance_end_ms,
                vad_events=True,
                endpointing=self.endpointing,
            )
            
            # Start the connection
            if not self.deepgram_connection.start(options):
                logger.error("Failed to start Deepgram connection")
                return
            
            # Create and start microphone
            self.microphone = Microphone(self.deepgram_connection.send)
            
            # Start microphone
            self.microphone.start()
            
            self.is_listening = True
            logger.info("Microphone opened and streaming...")
            
            # Keep the connection alive and check for finalization
            while not self.stop_event.is_set():
                # Check if we should finalize due to silence
                if self.current_transcript and time.time() - self.last_speech_time > self.silence_threshold:
                    self._finalize_transcript()
                
                time.sleep(self.poll_interval)
            
            # Cleanup
            if self.microphone:
                self.microphone.finish()
            
            if self.deepgram_connection:
                self.deepgram_connection.finish()
            
            self.is_listening = False
            logger.info("Stopped listening")
            
        except Exception as e:
            logger.error(f"Error in listening loop: {e}")
            self.is_listening = False
    
    def _check_and_finalize_transcript(self):
        """Check if enough silence has passed to finalize the transcript"""
        # Use a slightly lower threshold for immediate finalization on final results
        immediate_threshold = self.silence_threshold * 0.8
        if self.current_transcript and time.time() - self.last_speech_time > immediate_threshold:
            self._finalize_transcript()
    
    def _finalize_transcript(self):
        """Finalize and process the accumulated transcript"""
        if not self.current_transcript:
            return
        
        transcript = self.current_transcript.strip()
        if transcript:
            logger.info(f"Finalized transcript: {transcript}")
            
            # Put in queue
            self.transcription_queue.put(transcript)
            
            # Call callback if provided
            if self.on_transcription:
                try:
                    self.on_transcription(transcript)
                except Exception as e:
                    logger.error(f"Error in transcription callback: {e}")
        
        # Reset for next utterance
        self.current_transcript = ""
    
    def stop_listening(self):
        """Stop listening for speech"""
        if not self.is_listening:
            return
        
        logger.info("Stopping listening...")
        self.stop_event.set()
        
        # Wait for thread to finish
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=2.0)
        
        self.is_listening = False
    
    def get_transcription(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Get next transcription from queue
        
        Args:
            timeout: Maximum time to wait for transcription (None = blocking)
            
        Returns:
            Transcription text or None if timeout
        """
        try:
            return self.transcription_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def is_active(self) -> bool:
        """Check if STT service is currently listening"""
        return self.is_listening
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
    
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

def start_listening() -> bool:
    """
    Convenience function to start listening using global STT service
    
    Returns:
        True if listening started successfully, False otherwise
    """
    stt = get_stt_service()
    return stt.start_listening()

def stop_listening():
    """
    Convenience function to stop listening using global STT service
    """
    stt = get_stt_service()
    stt.stop_listening()

def get_transcription(timeout: Optional[float] = None) -> Optional[str]:
    """
    Convenience function to get transcription using global STT service
    
    Args:
        timeout: Maximum time to wait for transcription
        
    Returns:
        Transcription text or None if timeout
    """
    stt = get_stt_service()
    return stt.get_transcription(timeout=timeout)

def is_stt_available() -> bool:
    """Check if STT is available and configured"""
    stt = get_stt_service()
    return stt.enabled

