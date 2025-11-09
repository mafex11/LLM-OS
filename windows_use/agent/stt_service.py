"""
Speech-to-Text service using Deepgram for Yuki AI Agent
Provides continuous listening with automatic wake detection
"""

import os
import threading
import queue
import time
from typing import Optional, Callable
import logging
from pathlib import Path
import traceback

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
    Speech-to-Text service using Deepgram with continuous listening and trigger word detection
    """
    
    def __init__(self, api_key: Optional[str] = None, enable_stt: bool = True, 
                 on_transcription: Optional[Callable[[str], None]] = None,
                 latency_mode: str = "balanced", trigger_word: str = "yuki"):
        """
        Initialize STT service
        
        Args:
            api_key: Deepgram API key (if None, will try to get from env)
            enable_stt: Whether STT is enabled
            on_transcription: Callback function when transcription is received
            latency_mode: 'ultra' (100-200ms), 'fast' (300-500ms), or 'balanced' (800-1500ms, default)
            trigger_word: Trigger word to listen for (default: "yuki")
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
        self.trigger_word = trigger_word.lower()
        self.trigger_word_detected = False
        self.waiting_for_command = False
        # Conversation mode: after yuki trigger, accept queries without yuki for 2 minutes
        self.conversation_mode = False
        self.conversation_mode_timeout = 120.0  # 2 minutes in seconds
        self.last_query_time = None
        self.conversation_mode_lock = threading.Lock()
        self.conversation_timeout_thread = None
        
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
            logger.debug(f"Deepgram STT Service initialized successfully (latency_mode={self.latency_mode}, silence_threshold={self.silence_threshold}s)")
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram client: {e}")
            self.enabled = False
            return
    
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
        
        # Check if microphone is available before starting
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            if not input_devices:
                logger.error("No audio input devices found")
                return False
        except ImportError:
            # sounddevice not available, try to proceed anyway
            logger.warning("sounddevice not available for microphone check")
        except Exception as e:
            logger.warning(f"Could not check microphone availability: {e}")
            # Continue anyway, let the microphone initialization fail gracefully
        
        try:
            # Reset stop event and transcript tracking
            self.stop_event.clear()
            self._last_transcript = None  # Reset transcript tracking
            # Reset conversation mode state
            with self.conversation_mode_lock:
                self.conversation_mode = False
                self.last_query_time = None
            
            # Start conversation timeout monitoring thread
            self._start_conversation_timeout_monitor()
            
            # Start listening thread
            self.listening_thread = threading.Thread(
                target=self._listen_loop,
                daemon=True
            )
            self.listening_thread.start()
            
            # Wait briefly for microphone to open and streaming to begin
            # so callers can know if listening truly started
            start_deadline = time.time() + 5.0  # 5s timeout
            while time.time() < start_deadline:
                if self.is_listening:
                    return True
                # If thread died early, abort
                if self.listening_thread and not self.listening_thread.is_alive():
                    logger.error("Listening thread exited before start; microphone/connection failed")
                    return False
                time.sleep(0.05)
            logger.error("Timed out waiting for microphone to start streaming")
            return False
            
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
                        
                        logger.debug(f"Final transcript: {sentence}")
                        
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
                self.is_listening = False
                return
            
            # Create and start microphone with error handling
            try:
                self.microphone = Microphone(self.deepgram_connection.send)
                
                # Start microphone with timeout
                mic_started = threading.Event()
                mic_error = [None]
                
                def start_mic():
                    try:
                        self.microphone.start()
                        mic_started.set()
                    except Exception as e:
                        logger.error(f"Microphone start failed: {e}")
                        mic_error[0] = e
                        mic_started.set()
                
                # Start microphone in a separate thread with timeout
                mic_thread = threading.Thread(target=start_mic, daemon=True)
                mic_thread.start()
                
                # Wait for microphone to start or timeout after 5 seconds
                if not mic_started.wait(timeout=5.0):
                    raise Exception("Microphone initialization timed out")
                
                if mic_error[0]:
                    raise mic_error[0]
                    
            except Exception as mic_error:
                logger.error(f"Failed to initialize microphone: {mic_error}")
                # Clean up the connection
                if self.deepgram_connection:
                    try:
                        self.deepgram_connection.finish()
                    except:
                        pass
                self.is_listening = False
                return
            
            self.is_listening = True
            
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
            logger.debug("Stopped listening")
            
        except Exception as e:
            logger.error(f"Error in listening loop: {e}")
            self.is_listening = False
        finally:
            # Stop conversation timeout monitor
            self._stop_conversation_timeout_monitor()
    
    def _check_and_finalize_transcript(self):
        """Check if enough silence has passed to finalize the transcript"""
        # Use a slightly lower threshold for immediate finalization on final results
        immediate_threshold = self.silence_threshold * 0.8
        if self.current_transcript and time.time() - self.last_speech_time > immediate_threshold:
            self._finalize_transcript()
    
    def _finalize_transcript(self):
        """Finalize and process the accumulated transcript with trigger word detection"""
        if not self.current_transcript:
            return
        
        transcript = self.current_transcript.strip()
        if transcript:
            logger.debug(f"Finalized transcript: {transcript}")
            
            # Check for trigger word detection
            transcript_lower = transcript.lower()
            
            # Check if we're in conversation mode
            with self.conversation_mode_lock:
                in_conversation_mode = self.conversation_mode
            
            # Check if trigger word is present (even in conversation mode, to reset timeout)
            has_trigger_word = self.trigger_word in transcript_lower
            
            # If we're in conversation mode
            if in_conversation_mode:
                # If trigger word is present, extract command after it (if any)
                if has_trigger_word:
                    words = transcript_lower.split()
                    trigger_index = -1
                    
                    for i, word in enumerate(words):
                        if self.trigger_word in word:
                            trigger_index = i
                            break
                    
                    if trigger_index >= 0:
                        # Extract command after trigger word
                        if trigger_index + 1 < len(words):
                            # Command follows trigger word
                            command_words = words[trigger_index + 1:]
                            query = " ".join(command_words) if command_words else transcript
                        else:
                            # Only trigger word - use the full transcript (might be just "yuki")
                            # In conversation mode, if user says just "yuki", we can ignore it or reset timeout
                            # For now, we'll reset timeout but not process it as a query
                            if transcript_lower.strip() == self.trigger_word or transcript_lower.strip().startswith(self.trigger_word):
                                # Just "yuki" - reset timeout but don't process
                                with self.conversation_mode_lock:
                                    self.last_query_time = time.time()
                                    logger.debug("Trigger word detected in conversation mode - timeout reset")
                                self.current_transcript = ""
                                return
                            query = transcript
                    else:
                        query = transcript
                else:
                    # No trigger word - any transcript is a query
                    query = transcript
                
                # Reset the timeout - update last query time
                with self.conversation_mode_lock:
                    self.last_query_time = time.time()
                
                # Only process if query is not empty or just the trigger word
                if query.strip() and query.strip().lower() != self.trigger_word:
                    logger.debug(f"Query detected in conversation mode: {query}")
                    
                    # Put query in queue
                    self.transcription_queue.put(query)
                    
                    # Call callback if provided
                    if self.on_transcription:
                        try:
                            self.on_transcription(query)
                        except Exception as e:
                            logger.error(f"Error in transcription callback: {e}")
                else:
                    logger.debug(f"Empty query or just trigger word in conversation mode - timeout reset only")
                
                # Reset for next utterance
                self.current_transcript = ""
                return
            
            # If we're waiting for a command after trigger word was detected
            if self.waiting_for_command:
                # Any speech after trigger word is considered a command
                command = transcript
                logger.debug(f"Command detected: {command}")
                
                # Reset trigger word state
                self.waiting_for_command = False
                self.trigger_word_detected = False
                
                # Enter conversation mode and reset timeout
                with self.conversation_mode_lock:
                    self.conversation_mode = True
                    self.last_query_time = time.time()
                    logger.debug("Entered conversation mode - will accept queries without trigger word for 2 minutes")
                
                # Put command in queue
                self.transcription_queue.put(command)
                
                # Call callback if provided
                if self.on_transcription:
                    try:
                        self.on_transcription(command)
                    except Exception as e:
                        logger.error(f"Error in transcription callback: {e}")
            
            # Check if trigger word is present in the transcript (not in conversation mode)
            elif has_trigger_word:
                # Check if trigger word is at the beginning or followed by a command
                words = transcript_lower.split()
                trigger_index = -1
                
                for i, word in enumerate(words):
                    if self.trigger_word in word:
                        trigger_index = i
                        break
                
                if trigger_index >= 0:
                    # Extract command after trigger word
                    if trigger_index + 1 < len(words):
                        # Command follows trigger word
                        command_words = words[trigger_index + 1:]
                        command = " ".join(command_words)
                        
                        if command.strip():
                            logger.debug(f"Trigger word '{self.trigger_word}' detected with command: {command}")
                            
                            # Enter conversation mode and reset timeout
                            with self.conversation_mode_lock:
                                self.conversation_mode = True
                                self.last_query_time = time.time()
                                logger.debug("Entered conversation mode - will accept queries without trigger word for 2 minutes")
                            
                            # Put command in queue
                            self.transcription_queue.put(command)
                            
                            # Call callback if provided
                            if self.on_transcription:
                                try:
                                    self.on_transcription(command)
                                except Exception as e:
                                    logger.error(f"Error in transcription callback: {e}")
                        else:
                            # Trigger word detected but no command yet - wait for next utterance
                            logger.debug(f"Trigger word '{self.trigger_word}' detected, waiting for command...")
                            self.trigger_word_detected = True
                            self.waiting_for_command = True
                    else:
                        # Only trigger word detected - wait for next utterance
                        logger.debug(f"Trigger word '{self.trigger_word}' detected, waiting for command...")
                        self.trigger_word_detected = True
                        self.waiting_for_command = True
            else:
                # No trigger word detected and not in conversation mode - ignore the transcript
                logger.debug(f"No trigger word detected, ignoring: {transcript}")
        
        # Reset for next utterance
        self.current_transcript = ""
    
    def stop_listening(self):
        """Stop listening for speech"""
        if not self.is_listening:
            return
        
        logger.debug("Stopping listening...")
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
    
    def is_waiting_for_command(self) -> bool:
        """Check if service is waiting for a command after trigger word detection"""
        return self.waiting_for_command
    
    def reset_trigger_state(self):
        """Reset trigger word detection state"""
        self.trigger_word_detected = False
        self.waiting_for_command = False
    
    def _start_conversation_timeout_monitor(self):
        """Start the conversation timeout monitoring thread"""
        if self.conversation_timeout_thread and self.conversation_timeout_thread.is_alive():
            return
        
        def monitor_timeout():
            """Monitor conversation mode timeout"""
            while self.is_listening and not self.stop_event.is_set():
                try:
                    with self.conversation_mode_lock:
                        if self.conversation_mode and self.last_query_time is not None:
                            elapsed = time.time() - self.last_query_time
                            if elapsed >= self.conversation_mode_timeout:
                                # Timeout reached - exit conversation mode
                                logger.debug(f"Conversation mode timeout ({self.conversation_mode_timeout}s) reached, exiting conversation mode")
                                self.conversation_mode = False
                                self.last_query_time = None
                    time.sleep(1.0)  # Check every second
                except Exception as e:
                    logger.error(f"Error in conversation timeout monitor: {e}")
                    time.sleep(1.0)
        
        self.conversation_timeout_thread = threading.Thread(target=monitor_timeout, daemon=True)
        self.conversation_timeout_thread.start()
    
    def _stop_conversation_timeout_monitor(self):
        """Stop the conversation timeout monitoring thread"""
        # The thread will exit when is_listening becomes False or stop_event is set
        # No need to explicitly stop it, but we can wait for it if needed
        pass
    
    def reset_conversation_timeout(self):
        """Reset the conversation mode timeout (called after each query)"""
        with self.conversation_mode_lock:
            if self.conversation_mode:
                self.last_query_time = time.time()
                logger.debug("Conversation mode timeout reset")
    
    def is_in_conversation_mode(self) -> bool:
        """Check if service is in conversation mode"""
        with self.conversation_mode_lock:
            return self.conversation_mode
    
    def cleanup(self):
        """Clean up all resources"""
        try:
            self.stop_listening()
            
            # Clean up microphone
            if hasattr(self, 'microphone') and self.microphone:
                try:
                    self.microphone.finish()
                except:
                    pass
                self.microphone = None
            
            # Clean up Deepgram connection
            if hasattr(self, 'deepgram_connection') and self.deepgram_connection:
                try:
                    self.deepgram_connection.finish()
                except:
                    pass
                self.deepgram_connection = None
                
            # Clean up Deepgram client
            if hasattr(self, 'deepgram'):
                self.deepgram = None
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to clean up resources"""
        self.cleanup()


# Global STT service instance
_stt_service = None

def get_stt_service(trigger_word: str = "yuki") -> STTService:
    """Get or create global STT service instance"""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService(trigger_word=trigger_word)
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

