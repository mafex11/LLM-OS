"""
Activity tracking service.
Monitors app usage, tracks time spent, and records activity data.
"""

import logging
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Optional, Callable
from windows_use.tracking.storage import ActivityStorage
from windows_use.tracking.chrome_tracker import ChromeTracker
from windows_use.tracking.notification_service import NotificationService
from windows_use.desktop.service import Desktop

logger = logging.getLogger(__name__)


class ActivityTracker:
    """Tracks user activity including app usage and browser tabs."""
    
    def __init__(self, storage: ActivityStorage, desktop: Desktop, poll_interval: float = 2.0, 
                 notification_callback: Optional[Callable[[str, str], None]] = None,
                 llm=None, activity_analyzer=None):
        """
        Initialize activity tracker.
        
        Args:
            storage: ActivityStorage instance for data persistence
            desktop: Desktop service instance
            poll_interval: How often to check for activity changes (seconds)
            notification_callback: Optional callback for notifications (title, message)
            llm: Optional LLM instance for AI-based productivity classification
            activity_analyzer: Optional ActivityAnalyzer instance for classification
        """
        self.storage = storage
        self.desktop = desktop
        self.poll_interval = poll_interval
        
        self.chrome_tracker = ChromeTracker(desktop)
        self.app_categories = storage.get_app_categories()
        
        # Notification service with AI classification support
        self.notification_service = NotificationService(
            notification_callback=notification_callback,
            llm=llm,
            activity_analyzer=activity_analyzer
        )
        
        # Current activity state
        self.current_app: Optional[Dict] = None
        self.current_tab: Optional[Dict] = None
        self.current_activity_id: Optional[str] = None
        self.current_tab_id: Optional[str] = None
        self.activity_start_time: Optional[float] = None
        self.tab_start_time: Optional[float] = None
        
        # Track recent activities to resume them when switching back
        # Maps (app_name, window_title) -> (activity_id, last_end_time)
        self.recent_activities: Dict[tuple, tuple] = {}
        self.recent_tabs: Dict[tuple, tuple] = {}  # Maps (app_name, tab_url or tab_title) -> (activity_id, last_end_time)
        
        # Tracking state
        self.is_tracking = False
        self.tracking_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Batch writing for performance
        self.pending_activities = []
        self.last_write_time = time.time()
        self.write_interval = 5.0  # Write to disk every 5 seconds
        
        logger.info("Activity tracker initialized")
    
    def start_tracking(self):
        """Start activity tracking in background thread."""
        if self.is_tracking:
            logger.warning("Activity tracking already started")
            return
        
        self.is_tracking = True
        self.stop_event.clear()
        self.tracking_thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self.tracking_thread.start()
        logger.info("Activity tracking started")
    
    def stop_tracking(self):
        """Stop activity tracking."""
        if not self.is_tracking:
            return
        
        self.is_tracking = False
        self.stop_event.set()
        
        # Finalize current activity
        self._finalize_current_activity()
        self._finalize_current_tab()
        
        # Write pending activities
        self._write_pending_activities(force=True)
        
        # Wait for thread to finish
        if self.tracking_thread and self.tracking_thread.is_alive():
            self.tracking_thread.join(timeout=2.0)
        
        logger.info("Activity tracking stopped")
    
    def _tracking_loop(self):
        """Main tracking loop running in background thread."""
        logger.info("Tracking loop started")
        
        while not self.stop_event.is_set():
            try:
                self._check_activity()
                self._write_pending_activities()
                
                # Check for notifications (Netflix monitoring)
                current_app_activity = None
                if self.current_activity_id and self.current_app:
                    # Build current activity dict for notification service
                    current_app_activity = {
                        "app_name": self.current_app.get("name", ""),
                        "window_title": self.current_app.get("title", "")
                    }
                
                current_tab_activity = self.current_tab
                self.notification_service.check_activity(current_app_activity, current_tab_activity)
                
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in tracking loop: {e}")
                time.sleep(self.poll_interval)
        
        logger.info("Tracking loop stopped")
    
    def _check_activity(self):
        """Check for activity changes and update tracking."""
        try:
            desktop_state = self.desktop.get_state(use_vision=False)
            active_app = desktop_state.active_app
            
            if not active_app:
                # No active app, finalize current activity
                if self.current_activity_id:
                    self._finalize_current_activity()
                if self.current_tab_id:
                    self._finalize_current_tab()
                return
            
            # Get window title from the handle
            window_title = self._get_window_title(active_app.handle)
            
            current_app_info = {
                "name": active_app.name,
                "title": window_title,
                "process_id": active_app.handle  # Using handle as process identifier
            }
            
            # Check if Chrome/browser is active - handle tabs separately
            is_browser = self.chrome_tracker.is_chrome_active(active_app)
            
            if is_browser:
                # For browsers, track tabs separately (not app-level activities)
                # Finalize any app-level activity if we have one
                if self.current_activity_id and not self.current_tab_id:
                    self._finalize_current_activity()
                
                # Track tabs for browser
                tab_info = self.chrome_tracker.get_chrome_tab_info(active_app)
                
                if tab_info:
                    # Check if tab actually changed (by URL or significant title change)
                    if self.chrome_tracker.tab_changed(tab_info):
                        # Finalize previous tab
                        if self.current_tab_id:
                            self._finalize_current_tab()
                        
                        # Check if we can resume a recent tab activity
                        tab_url = tab_info.get("tab_url") or ""
                        tab_title = tab_info.get("tab_title") or ""
                        # Use URL as primary key, fallback to title if URL not available
                        # For browser tabs, extract browser name from window title (e.g., "Home / X - Comet" -> "Comet")
                        browser_app_name = active_app.name
                        if " - " in browser_app_name:
                            parts = browser_app_name.split(" - ")
                            if len(parts) > 1:
                                browser_app_name = parts[-1].strip()  # Get browser name from end
                        tab_key = (browser_app_name, tab_url if tab_url else tab_title)
                        resumed = self._try_resume_tab(tab_key, tab_info, current_app_info)
                        if not resumed:
                            # Start new tab activity
                            self._start_new_tab(tab_info, current_app_info)
                    else:
                        # Same tab, just update the title in case it changed slightly
                        # But don't create a new activity - extend the current one
                        if self.current_tab_id and self.current_tab:
                            # Update current tab info but keep same activity
                            self.current_tab["tab_title"] = tab_info.get("tab_title", "")
                            # Update the pending activity's title as well
                            for activity in self.pending_activities:
                                if activity.get("id") == self.current_tab_id:
                                    activity["tab_title"] = tab_info.get("tab_title", "")
                                    break
                else:
                    # Browser active but no tab info, finalize tab
                    if self.current_tab_id:
                        self._finalize_current_tab()
                
                # Update current_app for reference but don't create app-level activity
                self.current_app = current_app_info
            else:
                # Non-browser app - track as app activity
                # Finalize any tab activity if exists (switching away from browser)
                if self.current_tab_id:
                    self._finalize_current_tab()
                
                app_name = current_app_info["name"]
                app_name_changed = (
                    not self.current_app or
                    self.current_app.get("name") != current_app_info["name"]
                )
                
                if app_name_changed:
                    # Finalize previous activity
                    if self.current_activity_id:
                        self._finalize_current_activity()
                    
                    # Check if we can resume a recent activity for this app
                    # Use app name as key (ignore title variations)
                    activity_key = (current_app_info["name"], "")
                    resumed = self._try_resume_activity(activity_key, current_app_info)
                    if not resumed:
                        # Start new activity
                        self._start_new_activity(current_app_info)
                
                # Update window title for current activity but don't create new one
                if self.current_activity_id and self.current_app:
                    # Update title in pending activity if it exists
                    for activity in self.pending_activities:
                        if activity.get("id") == self.current_activity_id:
                            # Only update if title changed significantly (not minor variations)
                            old_title = activity.get("window_title", "")
                            if window_title and window_title != old_title:
                                # Update title but keep same activity
                                activity["window_title"] = window_title
                                self.current_app["title"] = window_title
                            break
        
        except Exception as e:
            logger.error(f"Error checking activity: {e}")
    
    def _start_new_activity(self, app_info: Dict):
        """Start tracking a new app activity."""
        # Browsers are tracked as tabs, not app activities
        # This method is only called for non-browser apps
        self.current_app = app_info
        self.activity_start_time = time.time()
        self.current_activity_id = str(uuid.uuid4())
        
        # Categorize app
        category = self._categorize_app(app_info["name"])
        
        activity = {
            "id": self.current_activity_id,
            "app_name": app_info["name"],
            "window_title": app_info.get("title", ""),
            "start_time": datetime.fromtimestamp(self.activity_start_time).isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "process_id": app_info.get("process_id"),
            "category": category
        }
        
        self.pending_activities.append(activity)
        logger.debug(f"Started tracking app: {app_info['name']}")
    
    def _finalize_current_activity(self):
        """Finalize current app activity."""
        if not self.current_activity_id or not self.activity_start_time:
            return
        
        end_time = time.time()
        duration = int(end_time - self.activity_start_time)
        
        # Update pending activity
        for activity in self.pending_activities:
            if activity.get("id") == self.current_activity_id:
                activity["end_time"] = datetime.fromtimestamp(end_time).isoformat()
                # Add to existing duration if this activity was resumed
                existing_duration = activity.get("duration_seconds", 0) or 0
                activity["duration_seconds"] = existing_duration + duration
                break
        
        # Also update in storage if already written
        if self.current_activity_id:
            # Get the accumulated duration from the pending activity
            accumulated_duration = duration
            for activity in self.pending_activities:
                if activity.get("id") == self.current_activity_id:
                    accumulated_duration = activity.get("duration_seconds", duration)
                    break
            
            self.storage.update_activity(
                self.current_activity_id,
                {
                    "end_time": datetime.fromtimestamp(end_time).isoformat(),
                    "duration_seconds": accumulated_duration
                }
            )
        
        # Remember this activity for potential resumption
        # Only remember non-browser activities (browsers use tab tracking)
        if self.current_app:
            app_name = self.current_app.get("name", "")
            # Check if this is a browser - if so, don't track in recent_activities
            is_browser_app = self.chrome_tracker.is_chrome_active_by_name(app_name)
            if not is_browser_app:
                activity_key = (app_name, self.current_app.get("title", ""))
                self.recent_activities[activity_key] = (self.current_activity_id, end_time)
        
        self.current_activity_id = None
        self.activity_start_time = None
        self.current_app = None
    
    def _start_new_tab(self, tab_info: Dict, app_info: Dict):
        """Start tracking a new Chrome tab."""
        self.current_tab = tab_info
        self.tab_start_time = time.time()
        self.current_tab_id = str(uuid.uuid4())
        
        # For browsers, use a normalized app name (extract from window title or use process name)
        # The window title often contains " - BrowserName" at the end
        app_name = app_info["name"]
        # Try to extract browser name from title (e.g., "Home / X - Comet" -> "Comet")
        # Or use the process name if available
        browser_name = app_name
        if " - " in app_name:
            parts = app_name.split(" - ")
            if len(parts) > 1:
                browser_name = parts[-1].strip()  # Get the browser name from the end
        
        activity = {
            "id": self.current_tab_id,
            "app_name": browser_name,  # Use normalized browser name, not full window title
            "tab_url": tab_info.get("tab_url"),
            "tab_title": tab_info.get("tab_title", ""),
            "start_time": datetime.fromtimestamp(self.tab_start_time).isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "category": tab_info.get("category", "browsing"),
            "is_research": tab_info.get("is_research", False),
            "is_entertainment": tab_info.get("is_entertainment", False)
        }
        
        self.pending_activities.append(activity)
        logger.debug(f"Started tracking tab: {tab_info.get('tab_title', 'Unknown')}")
    
    def _finalize_current_tab(self):
        """Finalize current tab activity."""
        if not self.current_tab_id or not self.tab_start_time:
            return
        
        end_time = time.time()
        duration = int(end_time - self.tab_start_time)
        
        # Update pending activity
        for activity in self.pending_activities:
            if activity.get("id") == self.current_tab_id:
                activity["end_time"] = datetime.fromtimestamp(end_time).isoformat()
                # Add to existing duration if this activity was resumed
                existing_duration = activity.get("duration_seconds", 0) or 0
                activity["duration_seconds"] = existing_duration + duration
                break
        
        # Also update in storage if already written
        if self.current_tab_id:
            # Get the accumulated duration from the pending activity
            accumulated_duration = duration
            for activity in self.pending_activities:
                if activity.get("id") == self.current_tab_id:
                    accumulated_duration = activity.get("duration_seconds", duration)
                    break
            
            self.storage.update_activity(
                self.current_tab_id,
                {
                    "end_time": datetime.fromtimestamp(end_time).isoformat(),
                    "duration_seconds": accumulated_duration
                }
            )
        
        # Remember this tab for potential resumption
        if self.current_tab and self.current_app:
            tab_url = self.current_tab.get("tab_url") or ""
            tab_title = self.current_tab.get("tab_title") or ""
            # Use normalized browser name for the key, not the full window title
            app_name = self.current_app.get("name", "")
            if " - " in app_name:
                parts = app_name.split(" - ")
                if len(parts) > 1:
                    app_name = parts[-1].strip()  # Get browser name from end
            tab_key = (app_name, tab_url if tab_url else tab_title)
            self.recent_tabs[tab_key] = (self.current_tab_id, end_time)
        
        self.current_tab_id = None
        self.tab_start_time = None
        self.current_tab = None
    
    def _categorize_app(self, app_name: str) -> str:
        """Categorize app based on configuration."""
        app_name_lower = app_name.lower()
        
        work_apps = self.app_categories.get("work_apps", [])
        entertainment_apps = self.app_categories.get("entertainment_apps", [])
        browser_apps = self.app_categories.get("browser_apps", [])
        
        if any(work_app in app_name_lower for work_app in work_apps):
            return "work"
        elif any(ent_app in app_name_lower for ent_app in entertainment_apps):
            return "entertainment"
        elif any(browser_app in app_name_lower for browser_app in browser_apps):
            return "browser"
        else:
            return "other"
    
    def _write_pending_activities(self, force: bool = False):
        """Write pending activities to storage."""
        current_time = time.time()
        
        if not force and (current_time - self.last_write_time) < self.write_interval:
            return
        
        if not self.pending_activities:
            return
        
        # Write all pending activities
        for activity in self.pending_activities:
            # Only write if activity is finalized (has end_time) or force write
            if force or activity.get("end_time") is not None:
                self.storage.append_activity(activity)
        
        # Remove written activities (keep ongoing ones)
        self.pending_activities = [
            act for act in self.pending_activities
            if act.get("end_time") is None
        ]
        
        self.last_write_time = current_time
    
    def _get_window_title(self, handle: int) -> str:
        """Get window title from window handle."""
        try:
            import ctypes
            length = ctypes.windll.user32.GetWindowTextLengthW(handle)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(handle, buffer, length + 1)
                return buffer.value
            return ""
        except Exception:
            return ""
    
    def get_current_activity(self) -> Optional[Dict]:
        """Get current activity information."""
        if not self.current_activity_id:
            return None
        
        # Ensure we have the latest window title
        if self.current_app and self.current_app.get("process_id"):
            self.current_app["title"] = self._get_window_title(self.current_app["process_id"])
        
        # Calculate total duration including any accumulated time
        base_duration = 0
        if self.current_activity_id:
            for activity in self.pending_activities:
                if activity.get("id") == self.current_activity_id:
                    base_duration = activity.get("duration_seconds", 0) or 0
                    break
        
        current_session_duration = int(time.time() - self.activity_start_time) if self.activity_start_time else 0
        total_duration = base_duration + current_session_duration
        
        return {
            "app": self.current_app,
            "tab": self.current_tab,
            "duration": total_duration
        }
    
    def _try_resume_activity(self, activity_key: tuple, app_info: Dict) -> bool:
        """Try to resume a recent activity for the same app/window."""
        if activity_key not in self.recent_activities:
            return False
        
        activity_id, last_end_time = self.recent_activities[activity_key]
        current_time = time.time()
        gap_seconds = current_time - last_end_time
        
        # Only resume if gap is less than 30 minutes (configurable threshold)
        resume_threshold = 30 * 60  # 30 minutes
        if gap_seconds > resume_threshold:
            return False
        
        # Find the activity in pending_activities or storage
        activity = None
        for act in self.pending_activities:
            if act.get("id") == activity_id:
                activity = act
                break
        
        # If not in pending, try to load from storage
        if not activity:
            # Load today's activities and find the one with this ID
            today = datetime.now().strftime("%Y-%m-%d")
            today_data = self.storage.get_activities(today)
            for act in today_data.get("app_activities", []):
                if act.get("id") == activity_id:
                    activity = dict(act)  # Make a copy
                    # Add it back to pending activities to resume
                    self.pending_activities.append(activity)
                    break
        
        if not activity:
            return False
        
        # Resume the activity
        self.current_activity_id = activity_id
        self.current_app = app_info
        self.activity_start_time = time.time()
        
        # Update the activity: remove end_time to make it ongoing again
        activity["end_time"] = None
        # Keep the accumulated duration if it exists
        if "duration_seconds" not in activity or activity["duration_seconds"] is None:
            activity["duration_seconds"] = 0
        
        logger.debug(f"Resumed activity for {app_info['name']} (gap: {int(gap_seconds)}s)")
        return True
    
    def _try_resume_tab(self, tab_key: tuple, tab_info: Dict, app_info: Dict) -> bool:
        """Try to resume a recent tab activity."""
        if tab_key not in self.recent_tabs:
            return False
        
        activity_id, last_end_time = self.recent_tabs[tab_key]
        current_time = time.time()
        gap_seconds = current_time - last_end_time
        
        # Only resume if gap is less than 30 minutes
        resume_threshold = 30 * 60  # 30 minutes
        if gap_seconds > resume_threshold:
            return False
        
        # Find the activity in pending_activities or storage
        activity = None
        for act in self.pending_activities:
            if act.get("id") == activity_id:
                activity = act
                break
        
        # If not in pending, try to load from storage
        if not activity:
            today = datetime.now().strftime("%Y-%m-%d")
            today_data = self.storage.get_activities(today)
            for act in today_data.get("tab_activities", []):
                if act.get("id") == activity_id:
                    activity = dict(act)  # Make a copy
                    self.pending_activities.append(activity)
                    break
        
        if not activity:
            return False
        
        # Resume the tab activity
        self.current_tab_id = activity_id
        self.current_tab = tab_info
        self.tab_start_time = time.time()
        
        # Update the activity: remove end_time to make it ongoing again
        activity["end_time"] = None
        # Keep the accumulated duration if it exists
        if "duration_seconds" not in activity or activity["duration_seconds"] is None:
            activity["duration_seconds"] = 0
        
        logger.debug(f"Resumed tab activity for {tab_info.get('tab_title', 'Unknown')} (gap: {int(gap_seconds)}s)")
        return True

