"""
Screenshot service for capturing periodic screenshots.
"""

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
from PIL import Image
import pyautogui

logger = logging.getLogger(__name__)


"""
class ScreenshotService:
    """Service for capturing screenshots periodically or on demand."""
    
    def __init__(self, storage, capture_interval: float = 300.0, on_capture: Optional[Callable] = None):
        """
        Initialize screenshot service.
        
        Args:
            storage: ActivityStorage instance for getting screenshot paths
            capture_interval: Interval between screenshots in seconds (default: 5 minutes)
            on_capture: Callback function called after each screenshot (receives file_path, timestamp)
        """
        self.storage = storage
        self.capture_interval = capture_interval
        self.on_capture = on_capture
        
        # Screenshot state
        self.is_capturing = False
        self.capture_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.last_capture_time: Optional[float] = None
        
        logger.info(f"Screenshot service initialized (interval: {capture_interval}s)")
    
    def start_capturing(self):
        """Start periodic screenshot capture."""
        if self.is_capturing:
            logger.warning("Screenshot capture already started")
            return
        
        self.is_capturing = True
        self.stop_event.clear()
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("Screenshot capture started")
    
    def stop_capturing(self):
        """Stop periodic screenshot capture."""
        if not self.is_capturing:
            return
        
        self.is_capturing = False
        self.stop_event.set()
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        logger.info("Screenshot capture stopped")
    
    def capture_now(self) -> Optional[Path]:
        """Capture screenshot immediately."""
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Generate filename with timestamp
            timestamp = datetime.now()
            filename = timestamp.strftime("%H-%M-%S.png")
            
            # Get storage path
            file_path = self.storage.get_screenshot_path(filename=filename)
            
            # Save screenshot
            screenshot.save(file_path, format='PNG', optimize=True)
            
            # Update metadata
            metadata = {
                "id": str(time.time()),
                "filename": filename,
                "file_path": str(file_path),
                "timestamp": timestamp.isoformat(),
                "file_size_bytes": file_path.stat().st_size if file_path.exists() else 0
            }
            
            self.storage.save_screenshot_metadata(metadata)
            
            # Call callback if provided
            if self.on_capture:
                try:
                    self.on_capture(file_path, timestamp)
                except Exception as e:
                    logger.error(f"Error in screenshot callback: {e}")
            
            self.last_capture_time = time.time()
            logger.debug(f"Screenshot captured: {file_path}")
            
            return file_path
        
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    def _capture_loop(self):
        """Main capture loop running in background thread."""
        logger.info("Screenshot capture loop started")
        
        # Capture immediately on start
        self.capture_now()
        
        while not self.stop_event.is_set():
            try:
                # Wait for capture interval
                self.stop_event.wait(timeout=self.capture_interval)
                
                if not self.stop_event.is_set():
                    self.capture_now()
            
            except Exception as e:
                logger.error(f"Error in screenshot capture loop: {e}")
                time.sleep(self.capture_interval)
        
        logger.info("Screenshot capture loop stopped")
    
    def set_capture_interval(self, interval: float):
        """Update capture interval."""
        self.capture_interval = interval
        logger.info(f"Screenshot capture interval updated to {interval}s")
"""


class ScreenshotService:
    """Disabled stub for screenshot capture."""
    
    def __init__(self, *args, **kwargs):
        logger.info("Screenshot service disabled; no screenshots will be captured.")
    
    def start_capturing(self):
        logger.debug("start_capturing() ignored because screenshot service is disabled.")
    
    def stop_capturing(self):
        logger.debug("stop_capturing() ignored because screenshot service is disabled.")
    
    def capture_now(self):
        logger.debug("capture_now() ignored because screenshot service is disabled.")
        return None
    
    def set_capture_interval(self, interval: float):
        logger.debug("set_capture_interval() ignored because screenshot service is disabled.")

