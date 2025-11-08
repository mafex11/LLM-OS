"""
JSON-based storage service for activity tracking data.
Stores data in local JSON files for Electron app compatibility.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import logging

logger = logging.getLogger(__name__)


class ActivityStorage:
    """Manages JSON file-based storage for activity tracking data."""
    
    def __init__(self, base_path: str = None):
        """
        Initialize storage with base path.
        
        Args:
            base_path: Base directory for storing data. If None, uses default data directory.
        """
        if base_path is None:
            # Use WINDOWS_USE_DATA_PATH (set by Electron) or fallback to YUKI_DATA_PATH or default
            base_path = os.getenv('WINDOWS_USE_DATA_PATH') or os.getenv('YUKI_DATA_PATH') or os.path.join(os.getcwd(), 'data')
        
        self.base_path = Path(base_path)
        self.activities_dir = self.base_path / "activities"
        self.screenshots_dir = self.base_path / "screenshots"
        self.summaries_dir = self.base_path / "summaries"
        self.metadata_dir = self.base_path / "metadata"
        
        # Create directories if they don't exist
        self.activities_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Activity storage initialized at: {self.base_path}")
    
    def get_today_file(self) -> Path:
        """Get today's activity file path."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.activities_dir / f"{today}.json"
    
    def _load_or_create_daily_data(self, date: str = None) -> Dict:
        """Load existing daily data or create new structure."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        file_path = self.activities_dir / f"{date}.json"
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading activity file {file_path}: {e}")
                # Return empty structure if file is corrupted
                return self._create_empty_daily_data(date)
        
        return self._create_empty_daily_data(date)
    
    def _create_empty_daily_data(self, date: str) -> Dict:
        """Create empty daily data structure."""
        return {
            "date": date,
            "app_activities": [],
            "tab_activities": [],
            "metadata": {
                "total_active_time": 0,
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def append_activity(self, activity: Dict):
        """Append activity to today's file."""
        file_path = self.get_today_file()
        data = self._load_or_create_daily_data()
        
        # Append activity based on type
        # Check if it's a browser activity - browsers should only be in tab_activities
        # Tab activities are tracked separately but not shown on activity page
        if "tab_url" in activity or "tab_title" in activity:
            # Has tab info - definitely a tab activity
            data["tab_activities"].append(activity)
        else:
            # Regular app activity
            data["app_activities"].append(activity)
        
        # Update metadata
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Save back to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving activity to {file_path}: {e}")
    
    def update_activity(self, activity_id: str, updates: Dict, date: str = None):
        """Update an existing activity by ID."""
        data = self._load_or_create_daily_data(date)
        
        # Search in app_activities
        for activity in data["app_activities"]:
            if activity.get("id") == activity_id:
                # Just update with the provided values (duration is already accumulated)
                activity.update(updates)
                activity["last_updated"] = datetime.now().isoformat()
                break
        else:
            # Search in tab_activities
            for activity in data["tab_activities"]:
                if activity.get("id") == activity_id:
                    # Just update with the provided values (duration is already accumulated)
                    activity.update(updates)
                    activity["last_updated"] = datetime.now().isoformat()
                    break
        
        # Save back to file
        file_path = self.activities_dir / f"{data['date']}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error updating activity in {file_path}: {e}")
    
    def get_activities(self, date: str = None) -> Dict:
        """Get activities for a specific date (default: today)."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        data = self._load_or_create_daily_data(date)
        
        # Merge consecutive activities of the same app/tab
        if data.get("app_activities"):
            data["app_activities"] = self._merge_consecutive_activities(data["app_activities"])
        if data.get("tab_activities"):
            data["tab_activities"] = self._merge_consecutive_activities(data["tab_activities"])
        
        return data
    
    def _merge_consecutive_activities(self, activities: List[Dict]) -> List[Dict]:
        """Merge consecutive activities of the same app/tab that should be one continuous session."""
        if not activities:
            return activities
        
        # Sort by start time
        sorted_activities = sorted(activities, key=lambda x: x.get("start_time", ""))
        merged = []
        
        for activity in sorted_activities:
            if not merged:
                merged.append(activity)
                continue
            
            last_activity = merged[-1]
            
            # Check if we can merge with the last activity
            if self._can_merge_activities(last_activity, activity):
                # Merge: extend end time and add duration
                last_end = datetime.fromisoformat(last_activity.get("end_time", last_activity.get("start_time")))
                current_start = datetime.fromisoformat(activity.get("start_time"))
                current_end = datetime.fromisoformat(activity.get("end_time", activity.get("start_time")))
                
                # Use the later end time
                if current_end > last_end:
                    last_activity["end_time"] = activity["end_time"]
                    # Recalculate total duration
                    total_start = datetime.fromisoformat(last_activity["start_time"])
                    total_duration = int((current_end - total_start).total_seconds())
                    last_activity["duration_seconds"] = total_duration
                
                # Update window/tab title if it changed (keep the most recent)
                if activity.get("window_title"):
                    last_activity["window_title"] = activity.get("window_title")
                if activity.get("tab_title"):
                    last_activity["tab_title"] = activity.get("tab_title")
                if activity.get("tab_url"):
                    last_activity["tab_url"] = activity.get("tab_url")
            else:
                # Cannot merge, add as new activity
                merged.append(activity)
        
        return merged
    
    def _can_merge_activities(self, activity1: Dict, activity2: Dict) -> bool:
        """Check if two activities can be merged into one continuous session."""
        # Both must be finalized (have end times)
        if not activity1.get("end_time") or not activity2.get("start_time"):
            return False
        
        # Check if they're the same app
        if activity1.get("app_name") != activity2.get("app_name"):
            return False
        
        # Check time gap - merge if gap is less than 5 minutes (likely same session)
        try:
            end1 = datetime.fromisoformat(activity1["end_time"])
            start2 = datetime.fromisoformat(activity2["start_time"])
            gap_seconds = (start2 - end1).total_seconds()
            
            # If gap is more than 5 minutes, they're separate sessions
            if gap_seconds > 300:  # 5 minutes
                return False
            
            # For tab activities, check if it's the same tab
            if "tab_url" in activity1 or "tab_url" in activity2:
                url1 = activity1.get("tab_url") or ""
                url2 = activity2.get("tab_url") or ""
                # If URLs are different, don't merge (different tabs)
                if url1 and url2 and url1 != url2:
                    return False
                
                # For same URL, check if titles are similar enough
                title1 = activity1.get("tab_title", "").lower()
                title2 = activity2.get("tab_title", "").lower()
                if title1 and title2:
                    # Extract base titles (remove YouTube, Chrome suffixes)
                    base1 = self._extract_base_title(title1)
                    base2 = self._extract_base_title(title2)
                    # If base titles are similar (more than 70% same words), merge
                    similarity = self._calculate_title_similarity(base1, base2)
                    if similarity < 0.7:
                        return False
            
            # Same app, small gap, merge them
            return True
        except Exception:
            # If parsing fails, don't merge
            return False
    
    def _extract_base_title(self, title: str) -> str:
        """Extract base title without common suffixes."""
        title_lower = title.lower().strip()
        suffixes = [" - youtube", " - chrome", " - firefox", " - edge", " - google chrome", " - microsoft edge"]
        for suffix in suffixes:
            if title_lower.endswith(suffix):
                return title_lower[:-len(suffix)].strip()
        return title_lower
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles (0.0 to 1.0)."""
        if not title1 or not title2:
            return 0.0
        
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def get_activities_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get activities for a date range."""
        activities = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            day_activities = self.get_activities(date_str)
            activities.append(day_activities)
            current += timedelta(days=1)
        
        return activities
    
    def save_screenshot_metadata(self, metadata: Dict):
        """Save screenshot metadata."""
        date = metadata.get("date", datetime.now().strftime("%Y-%m-%d"))
        date_dir = self.screenshots_dir / date
        date_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = date_dir / "screenshot-metadata.json"
        
        # Load existing metadata or create new
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading screenshot metadata: {e}")
                data = {"date": date, "screenshots": []}
        else:
            data = {"date": date, "screenshots": []}
        
        # Append screenshot metadata
        data["screenshots"].append(metadata)
        
        # Save back to file
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving screenshot metadata: {e}")
    
    def get_screenshot_metadata(self, date: str = None) -> List[Dict]:
        """Get screenshot metadata for a specific date."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        metadata_file = self.screenshots_dir / date / "screenshot-metadata.json"
        
        if not metadata_file.exists():
            return []
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("screenshots", [])
        except Exception as e:
            logger.error(f"Error loading screenshot metadata: {e}")
            return []
    
    def save_daily_summary(self, summary: Dict):
        """Save daily summary."""
        date = summary.get("date", datetime.now().strftime("%Y-%m-%d"))
        summary_file = self.summaries_dir / f"{date}.json"
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving daily summary: {e}")
    
    def get_daily_summary(self, date: str = None) -> Optional[Dict]:
        """Get daily summary for a specific date."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        summary_file = self.summaries_dir / f"{date}.json"
        
        if not summary_file.exists():
            return None
        
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading daily summary: {e}")
            return None
    
    def get_summaries_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get summaries for a date range."""
        summaries = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            summary = self.get_daily_summary(date_str)
            if summary:
                summaries.append(summary)
            current += timedelta(days=1)
        
        return summaries
    
    def get_app_categories(self) -> Dict:
        """Load app categorization configuration."""
        categories_file = self.metadata_dir / "app_categories.json"
        
        if categories_file.exists():
            try:
                with open(categories_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading app categories: {e}")
        
        # Return default categories if file doesn't exist
        return self._get_default_categories()
    
    def _get_default_categories(self) -> Dict:
        """Get default app categorization."""
        return {
            "work_apps": [
                "code",
                "visual studio code",
                "pycharm",
                "excel",
                "outlook",
                "teams",
                "notepad",
                "notepad++"
            ],
            "entertainment_apps": [
                "spotify",
                "discord",
                "steam",
                "vlc"
            ],
            "browser_apps": [
                "chrome",
                "firefox",
                "edge",
                "msedge"
            ],
            "research_patterns": [
                "stackoverflow.com",
                "docs.python.org",
                "github.com",
                "wikipedia.org",
                "*.edu"
            ],
            "entertainment_patterns": [
                "youtube.com",
                "netflix.com",
                "twitch.tv",
                "reddit.com",
                "twitter.com",
                "x.com",
                "instagram.com",
                "facebook.com"
            ]
        }
    
    def save_app_categories(self, categories: Dict):
        """Save app categorization configuration."""
        categories_file = self.metadata_dir / "app_categories.json"
        
        try:
            with open(categories_file, 'w', encoding='utf-8') as f:
                json.dump(categories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving app categories: {e}")
    
    def get_screenshot_path(self, date: str = None, filename: str = None) -> Path:
        """Get path for screenshot storage."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        date_dir = self.screenshots_dir / date
        date_dir.mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime("%H-%M-%S")
            filename = f"{timestamp}.png"
        
        return date_dir / filename

