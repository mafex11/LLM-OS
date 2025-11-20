"""
Configuration and initialization for activity tracking.
"""

import os
import json
import logging
from typing import Optional, Callable
from windows_use.tracking.storage import ActivityStorage
from windows_use.tracking.service import ActivityTracker
from windows_use.tracking.analyzer import ActivityAnalyzer
# Screenshot analysis temporarily disabled across the stack
# from windows_use.tracking.screenshot_service import ScreenshotService
from windows_use.desktop.service import Desktop

logger = logging.getLogger(__name__)


def initialize_tracking(
    desktop: Desktop,
    storage_path: Optional[str] = None,
    google_api_key: Optional[str] = None,
    enable_screenshots: bool = True,
    screenshot_interval: float = 300.0,
    poll_interval: float = 2.0,
    notification_callback: Optional[Callable[[str, str], None]] = None,
    llm=None
) -> tuple:
    """
    Initialize activity tracking system.
    
    Args:
        desktop: Desktop service instance
        storage_path: Path for data storage (default: from environment or data directory)
        google_api_key: Google API key for AI analysis (optional)
        enable_screenshots: Whether to enable screenshot capture
        screenshot_interval: Screenshot capture interval in seconds (default: 5 minutes)
        poll_interval: Activity polling interval in seconds (default: 2 seconds)
        notification_callback: Optional callback function(title, message) for notifications
        llm: Optional LLM instance for AI-based productivity classification
    
    Returns:
        Tuple of (ActivityTracker, ScreenshotService, ActivityAnalyzer)
    """
    # Initialize storage
    storage = ActivityStorage(storage_path)
    
    # Initialize analyzer (use provided LLM if available, otherwise create new one)
    if llm:
        analyzer = ActivityAnalyzer(llm=llm)
    else:
        analyzer = ActivityAnalyzer(google_api_key=google_api_key)
    
    # Initialize activity tracker with notification callback and AI support
    tracker = ActivityTracker(
        storage, desktop, poll_interval=poll_interval, 
        notification_callback=notification_callback,
        llm=llm or (analyzer.llm if analyzer else None),
        activity_analyzer=analyzer
    )
    
    # Initialize screenshot service
    screenshot_service = None
    # Screenshot capture/analysis disabled temporarily.
    # if enable_screenshots:
    #     def on_screenshot_capture(file_path: Path, timestamp):
    #         """Callback when screenshot is captured - analyze it."""
    #         ...
    #     screenshot_service = ScreenshotService(
    #         storage,
    #         capture_interval=screenshot_interval,
    #         on_capture=on_screenshot_capture
    #     )
    
    # Create default configuration files if they don't exist
    _create_default_configs(storage)
    
    logger.info("Activity tracking system initialized")
    
    return tracker, screenshot_service, analyzer


def _create_default_configs(storage: ActivityStorage):
    """Create default configuration files if they don't exist."""
    try:
        # Check if app categories file exists
        categories_file = storage.metadata_dir / "app_categories.json"
        if not categories_file.exists():
            default_categories = storage._get_default_categories()
            storage.save_app_categories(default_categories)
            logger.info("Created default app categories configuration")
    except Exception as e:
        logger.error(f"Error creating default configs: {e}")

