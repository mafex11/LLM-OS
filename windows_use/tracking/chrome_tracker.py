"""
Chrome tab tracking service.
Tracks active Chrome tabs and their URLs/titles.
"""

import logging
import re
from typing import Dict, Optional, List
from windows_use.desktop.service import Desktop
from windows_use.desktop.views import App

logger = logging.getLogger(__name__)


class ChromeTracker:
    """Tracks Chrome browser tabs and their activity."""
    
    def __init__(self, desktop: Desktop):
        """
        Initialize Chrome tracker.
        
        Args:
            desktop: Desktop service instance for UI automation
        """
        self.desktop = desktop
        self.last_tab_info: Optional[Dict] = None
        self.chrome_process_names = ['chrome', 'google chrome', 'msedge', 'edge', 'firefox', 'comet']
    
    def is_chrome_active(self, active_app: Optional[App] = None) -> bool:
        """Check if Chrome (or any browser) is the active application."""
        if active_app is None:
            try:
                desktop_state = self.desktop.get_state(use_vision=False)
                active_app = desktop_state.active_app
            except Exception as e:
                logger.error(f"Error getting desktop state: {e}")
                return False
        
        if not active_app:
            return False
        
        # Check process name first (more reliable), then fall back to window title
        if active_app.process_name:
            process_name_lower = active_app.process_name.lower()
            # Remove .exe extension for comparison
            if process_name_lower.endswith('.exe'):
                process_name_lower = process_name_lower[:-4]
            if any(browser in process_name_lower for browser in self.chrome_process_names):
                return True
        
        # Fallback: check window title
        app_name_lower = active_app.name.lower()
        return any(browser in app_name_lower for browser in self.chrome_process_names)
    
    def is_chrome_active_by_name(self, app_name: str) -> bool:
        """Check if an app name indicates it's a browser."""
        if not app_name:
            return False
        app_name_lower = app_name.lower()
        return any(browser in app_name_lower for browser in self.chrome_process_names)
    
    def get_chrome_tab_info(self, active_app: Optional[App] = None) -> Optional[Dict]:
        """
        Extract tab information from Chrome window title.
        
        Chrome window titles typically contain:
        - Tab title (e.g., "YouTube - Watch")
        - URL patterns in some cases
        
        Returns:
            Dict with tab_url, tab_title, and category if available
        """
        if not self.is_chrome_active(active_app):
            return None
        
        if active_app is None:
            try:
                desktop_state = self.desktop.get_state(use_vision=False)
                active_app = desktop_state.active_app
            except Exception as e:
                logger.error(f"Error getting desktop state: {e}")
                return None
        
        if not active_app:
            return None
        
        # Get window title from the handle
        window_title = self._get_window_title(active_app.handle)
        if not window_title:
            return None
        tab_info = {
            "tab_title": window_title,
            "tab_url": None,
            "category": None,
            "is_research": False,
            "is_entertainment": False
        }
        
        # Try to extract URL from title (Chrome sometimes includes it)
        url_pattern = r'https?://[^\s]+'
        url_match = re.search(url_pattern, window_title)
        if url_match:
            tab_info["tab_url"] = url_match.group(0)
        
        # Categorize based on title patterns
        title_lower = window_title.lower()
        
        # Research patterns
        research_keywords = [
            'stackoverflow', 'stack overflow',
            'github.com', 'github',
            'docs.', 'documentation',
            'wikipedia',
            'medium.com', 'dev.to',
            'edu', '.edu',
            'tutorial', 'guide', 'how to'
        ]
        
        # Entertainment patterns
        entertainment_keywords = [
            'youtube', 'youtu.be',
            'netflix',
            'twitch',
            'reddit',
            'twitter', 'x.com',
            'instagram',
            'facebook',
            'tiktok'
        ]
        
        # Check for research patterns
        if any(keyword in title_lower for keyword in research_keywords):
            tab_info["category"] = "research"
            tab_info["is_research"] = True
        
        # Check for entertainment patterns
        elif any(keyword in title_lower for keyword in entertainment_keywords):
            tab_info["category"] = "entertainment"
            tab_info["is_entertainment"] = True
        
        # If URL is available, categorize based on domain
        if tab_info["tab_url"]:
            domain = self._extract_domain(tab_info["tab_url"])
            tab_info["category"] = self._categorize_domain(domain)
            if tab_info["category"] == "research":
                tab_info["is_research"] = True
            elif tab_info["category"] == "entertainment":
                tab_info["is_entertainment"] = True
        
        # If no category found, default to "browsing"
        if not tab_info["category"]:
            tab_info["category"] = "browsing"
        
        return tab_info
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            # Remove protocol
            if '://' in url:
                url = url.split('://', 1)[1]
            
            # Remove path and query
            if '/' in url:
                url = url.split('/', 1)[0]
            
            # Remove port
            if ':' in url:
                url = url.split(':', 1)[0]
            
            return url.lower()
        except Exception:
            return ""
    
    def _categorize_domain(self, domain: str) -> Optional[str]:
        """Categorize domain based on patterns."""
        if not domain:
            return None
        
        # Research domains
        research_domains = [
            'stackoverflow.com',
            'github.com',
            'wikipedia.org',
            'docs.python.org',
            'medium.com',
            'dev.to',
            'stackexchange.com'
        ]
        
        # Entertainment domains
        entertainment_domains = [
            'youtube.com',
            'youtu.be',
            'netflix.com',
            'twitch.tv',
            'reddit.com',
            'twitter.com',
            'x.com',
            'instagram.com',
            'facebook.com',
            'tiktok.com'
        ]
        
        # Check exact match
        if domain in research_domains:
            return "research"
        if domain in entertainment_domains:
            return "entertainment"
        
        # Check partial match (subdomains)
        for research_domain in research_domains:
            if research_domain in domain or domain.endswith('.' + research_domain):
                return "research"
        
        for entertainment_domain in entertainment_domains:
            if entertainment_domain in domain or domain.endswith('.' + entertainment_domain):
                return "entertainment"
        
        # Check for .edu domains
        if domain.endswith('.edu'):
            return "research"
        
        return None
    
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
    
    def tab_changed(self, current_tab_info: Optional[Dict]) -> bool:
        """Check if tab has changed since last check."""
        if current_tab_info is None:
            return self.last_tab_info is not None
        
        if self.last_tab_info is None:
            self.last_tab_info = current_tab_info
            return True
        
        # Compare tab info - only consider it changed if URL changed
        # or if title changed significantly (more than just minor updates)
        current_url = current_tab_info.get("tab_url") or ""
        last_url = self.last_tab_info.get("tab_url") or ""
        
        current_title = current_tab_info.get("tab_title") or ""
        last_title = self.last_tab_info.get("tab_title") or ""
        
        # URL change = definitely new tab
        if current_url and last_url and current_url != last_url:
            self.last_tab_info = current_tab_info
            return True
        
        # Title change only matters if URL is not available
        # But ignore minor title variations (e.g., YouTube progress updates)
        if not current_url and not last_url:
            # If titles are very different (more than 50% different), consider it changed
            if self._titles_different(current_title, last_title):
                self.last_tab_info = current_tab_info
                return True
        
        # Update last tab info with current title (in case it changed slightly)
        # but don't consider it a new tab
        self.last_tab_info["tab_title"] = current_title
        return False
    
    def _titles_different(self, title1: str, title2: str) -> bool:
        """Check if two titles are significantly different."""
        if not title1 or not title2:
            return title1 != title2
        
        # Normalize titles (remove common prefixes/suffixes)
        title1_norm = title1.lower().strip()
        title2_norm = title2.lower().strip()
        
        # If titles are exactly the same, no change
        if title1_norm == title2_norm:
            return False
        
        # Extract base title (remove common patterns like " - YouTube", " - Chrome", etc.)
        def extract_base(title):
            # Remove common suffixes
            for suffix in [" - youtube", " - chrome", " - firefox", " - edge", " - google chrome"]:
                if title.endswith(suffix):
                    return title[:-len(suffix)].strip()
            return title
        
        base1 = extract_base(title1_norm)
        base2 = extract_base(title2_norm)
        
        # If base titles are the same, it's likely the same tab with minor updates
        if base1 == base2:
            return False
        
        # Check similarity - if more than 70% similar, consider it the same tab
        # This handles cases like "Video Title - YouTube" vs "Video Title (5:30/10:00) - YouTube"
        similarity = self._calculate_similarity(base1, base2)
        if similarity > 0.7:
            return False
        
        return True
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0.0 to 1.0)."""
        if not str1 or not str2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)

