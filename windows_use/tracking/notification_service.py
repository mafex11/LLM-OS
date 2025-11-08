"""
Notification service for activity tracking.
Monitors user activity and sends notifications for focus reminders.
Uses AI to determine if activities are productive or not.
"""

import logging
import time
import threading
from typing import Dict, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for monitoring activities and sending notifications."""
    
    def __init__(self, notification_callback: Optional[Callable[[str, str], None]] = None,
                 llm=None, activity_analyzer=None):
        """
        Initialize notification service.
        
        Args:
            notification_callback: Callback function(title, message) to send notifications
            llm: Optional LLM instance for AI-based productivity classification
            activity_analyzer: Optional ActivityAnalyzer instance for classification
        """
        self.notification_callback = notification_callback
        self.llm = llm
        self.activity_analyzer = activity_analyzer
        
        # Tracking state
        self.current_activity_start_time: Optional[float] = None
        self.current_activity_info: Optional[Dict] = None
        self.current_activity_is_productive: Optional[bool] = None
        self.last_notification_time: Optional[float] = None
        self.notification_cooldown = 60 * 10  # 10 minutes cooldown between notifications
        
        # Classification cache to avoid repeated AI calls
        self.classification_cache: Dict[str, tuple] = {}  # key -> (is_productive, timestamp)
        self.cache_ttl = 60 * 30  # Cache classifications for 30 minutes
        
        # Configuration
        self.non_productive_threshold_seconds = 60 * 5  # 5 minutes
        self.notification_title = "Focus Reminder"
        
        logger.info("Notification service initialized with AI classification")
    
    def check_activity(self, current_activity: Optional[Dict], current_tab: Optional[Dict]):
        """
        Check current activity and send notifications if needed.
        Uses AI to determine if the activity is productive.
        
        Args:
            current_activity: Current app activity (if any)
            current_tab: Current tab activity (if any)
        """
        try:
            current_time = time.time()
            
            # Get activity identifier to track continuity
            activity_key = self._get_activity_key(current_activity, current_tab)
            
            # Check if activity changed
            if activity_key != self._get_current_activity_key():
                # Activity changed - check previous activity and reset
                if self.current_activity_start_time and not self.current_activity_is_productive:
                    # Previous activity was non-productive, but user switched away
                    logger.debug(f"User switched away from non-productive activity: {self.current_activity_info}")
                
                # Reset tracking for new activity
                self.current_activity_start_time = current_time
                self.current_activity_info = {
                    "activity": current_activity,
                    "tab": current_tab,
                    "key": activity_key
                }
                self.current_activity_is_productive = None  # Will be classified
            
            # Classify current activity if not already classified
            if self.current_activity_is_productive is None and activity_key:
                self.current_activity_is_productive = self._classify_activity_productivity(
                    current_activity, current_tab
                )
            
            # If activity is non-productive, check duration
            if activity_key and not self.current_activity_is_productive:
                if self.current_activity_start_time:
                    duration = current_time - self.current_activity_start_time
                    
                    # Check if threshold exceeded
                    if duration >= self.non_productive_threshold_seconds:
                        # Check cooldown
                        if (self.last_notification_time is None or 
                            (current_time - self.last_notification_time) >= self.notification_cooldown):
                            # Generate personalized message
                            message = self._generate_notification_message(
                                current_activity, current_tab, duration
                            )
                            
                            # Send notification
                            self._send_notification(
                                self.notification_title,
                                message
                            )
                            self.last_notification_time = current_time
                            logger.info(f"Sent focus notification for non-productive activity (duration: {int(duration)}s)")
            elif not activity_key:
                # No activity - reset
                self.current_activity_start_time = None
                self.current_activity_info = None
                self.current_activity_is_productive = None
                
        except Exception as e:
            logger.error(f"Error checking activity for notifications: {e}")
    
    def _get_activity_key(self, current_activity: Optional[Dict], current_tab: Optional[Dict]) -> Optional[str]:
        """Get a unique key for the current activity."""
        if current_tab:
            # Use tab URL or title as key
            tab_url = current_tab.get("tab_url") or ""
            tab_title = current_tab.get("tab_title") or ""
            if tab_url:
                return f"tab:{tab_url}"
            elif tab_title:
                return f"tab:{tab_title}"
        
        if current_activity:
            # Use app name and window title as key
            app_name = current_activity.get("app_name") or ""
            window_title = current_activity.get("window_title") or ""
            return f"app:{app_name}:{window_title}"
        
        return None
    
    def _get_current_activity_key(self) -> Optional[str]:
        """Get the key of the currently tracked activity."""
        if self.current_activity_info:
            return self.current_activity_info.get("key")
        return None
    
    def _classify_activity_productivity(self, current_activity: Optional[Dict], 
                                       current_tab: Optional[Dict]) -> bool:
        """
        Use AI to classify if an activity is productive or not.
        Returns True if productive, False if not.
        """
        try:
            # Build activity description
            activity_desc = self._build_activity_description(current_activity, current_tab)
            
            if not activity_desc:
                # No activity to classify
                return True  # Default to productive if unclear
            
            # Check cache first
            cache_key = activity_desc.lower().strip()
            if cache_key in self.classification_cache:
                is_productive, cached_time = self.classification_cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    logger.debug(f"Using cached classification for: {activity_desc[:50]}")
                    return is_productive
            
            # Use AI to classify - no fallbacks
            if self.llm:
                is_productive = self._classify_with_llm(activity_desc)
            elif self.activity_analyzer and self.activity_analyzer.llm:
                is_productive = self._classify_with_llm(activity_desc, self.activity_analyzer.llm)
            else:
                # No LLM available - default to productive (no notifications without AI)
                logger.warning(f"No LLM available for classification - defaulting to productive: {activity_desc[:50]}")
                is_productive = True
            
            # Cache the result
            self.classification_cache[cache_key] = (is_productive, time.time())
            
            # Clean old cache entries
            self._clean_cache()
            
            logger.debug(f"Classified activity as {'productive' if is_productive else 'non-productive'}: {activity_desc[:50]}")
            return is_productive
            
        except Exception as e:
            logger.error(f"Error classifying activity productivity: {e}")
            # Default to productive on error to avoid false positives
            return True
    
    def _build_activity_description(self, current_activity: Optional[Dict], 
                                   current_tab: Optional[Dict]) -> str:
        """Build a description of the current activity for AI classification."""
        parts = []
        
        if current_tab:
            tab_url = current_tab.get("tab_url") or ""
            tab_title = current_tab.get("tab_title") or ""
            if tab_url:
                parts.append(f"Browser tab: {tab_url}")
            if tab_title:
                parts.append(f"Tab title: {tab_title}")
        
        if current_activity:
            app_name = current_activity.get("app_name") or ""
            window_title = current_activity.get("window_title") or ""
            if app_name:
                parts.append(f"Application: {app_name}")
            if window_title:
                parts.append(f"Window: {window_title}")
        
        return " | ".join(parts) if parts else ""
    
    def _classify_with_llm(self, activity_desc: str, llm=None) -> bool:
        """Use LLM to classify if activity is productive."""
        try:
            llm_to_use = llm or self.llm
            if not llm_to_use:
                return True  # Default to productive
            
            from langchain_core.messages import HumanMessage
            
            prompt = f"""Analyze this user activity and determine if it is productive or not at this specific moment in time.

Activity: {activity_desc}

Consider the context:
- Productive activities: work tasks, coding/programming, writing documents, research for work/learning, professional development, important communication, work-related browsing, educational content
- Non-productive activities: entertainment videos (YouTube, Netflix, Amazon Prime, Hulu, Disney+), anime/streaming sites, gaming, social media scrolling, shopping for non-work items, time-wasting sites, distractions

Important: Consider the specific context. For example:
- YouTube could be productive if it's educational/tutorial content
- Amazon could be productive if it's work-related research
- But if it's clearly entertainment, streaming, or time-wasting, it's non-productive

Based on the activity description above, determine if this is productive or non-productive RIGHT NOW.

Respond with ONLY "productive" or "non-productive" (no other text)."""
            
            response = llm_to_use.invoke([HumanMessage(content=prompt)])
            result_text = response.content.strip().lower() if hasattr(response, 'content') else str(response).lower()
            
            # Parse response
            if "non-productive" in result_text or "not productive" in result_text:
                return False
            elif "productive" in result_text:
                return True
            else:
                # Default to productive if unclear
                logger.warning(f"Unclear LLM response for productivity classification: {result_text}")
                return True
                
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            # Default to productive on error
            return True
    
    
    def _generate_notification_message(self, current_activity: Optional[Dict], 
                                      current_tab: Optional[Dict], 
                                      duration_seconds: float) -> str:
        """Generate a personalized notification message."""
        # Build activity name
        activity_name = "this activity"
        
        if current_tab:
            tab_title = current_tab.get("tab_title") or ""
            if tab_title:
                # Extract meaningful part of title (remove browser suffixes)
                title_parts = tab_title.split(" - ")
                if title_parts:
                    activity_name = title_parts[0]
        
        if current_activity and activity_name == "this activity":
            app_name = current_activity.get("app_name") or ""
            window_title = current_activity.get("window_title") or ""
            if window_title:
                activity_name = window_title.split(" - ")[0]
            elif app_name:
                activity_name = app_name
        
        # Format duration
        minutes = int(duration_seconds / 60)
        duration_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
        
        return f"You've been on {activity_name} for {duration_str}. Time to focus on work!"
    
    def _clean_cache(self):
        """Clean old entries from classification cache."""
        current_time = time.time()
        keys_to_remove = [
            key for key, (_, cached_time) in self.classification_cache.items()
            if current_time - cached_time > self.cache_ttl
        ]
        for key in keys_to_remove:
            del self.classification_cache[key]
    
    def _send_notification(self, title: str, message: str):
        """Send notification via callback."""
        if self.notification_callback:
            try:
                self.notification_callback(title, message)
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
        else:
            logger.warning("No notification callback registered")
    
    def set_notification_callback(self, callback: Callable[[str, str], None]):
        """Set notification callback function."""
        self.notification_callback = callback
        logger.info("Notification callback registered")
    
    def set_llm(self, llm):
        """Set LLM instance for AI classification."""
        self.llm = llm
        logger.info("LLM instance set for notification service")
    
    def set_activity_analyzer(self, activity_analyzer):
        """Set ActivityAnalyzer instance for classification."""
        self.activity_analyzer = activity_analyzer
        logger.info("ActivityAnalyzer instance set for notification service")

