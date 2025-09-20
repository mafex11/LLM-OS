"""
Adaptive Detection System

This module provides smart, performance-optimized element detection that chooses
the right detection method based on task complexity and requirements.
"""

from uiautomation import Control, GetRootControl, GetFocusedControl, ControlType
from windows_use.tree.views import TreeElementNode, TextElementNode, ScrollElementNode, TreeState
from windows_use.desktop.intelligent_detector import IntelligentDetector, TaskType
from typing import List, Tuple, Optional, Dict, Any
import time
import re
from enum import Enum

class DetectionMode(Enum):
    FAST = "fast"           # Direct detection for simple actions
    SMART = "smart"         # Intelligent detection for complex tasks
    CACHED = "cached"       # Use cached coordinates
    FOCUSED = "focused"     # Focus-based detection only

class AdaptiveDetector:
    """
    Adaptive detector that chooses the optimal detection method for each task.
    """
    
    def __init__(self, desktop):
        self.desktop = desktop
        self.intelligent_detector = IntelligentDetector(desktop)
        self.coordinate_cache = {}
        self.element_cache = {}
        self.cache_timeout = 30.0  # Cache coordinates for 30 seconds
        self.last_refresh_time = 0
        self.focused_control = None
        
        # Common element patterns for fast detection
        self.common_patterns = {
            'new_tab': ['new tab', 'newtab', '+', 'add tab'],
            'address_bar': ['address', 'url', 'omnibox', 'location'],
            'search_box': ['search', 'find', 'query'],
            'submit_button': ['submit', 'go', 'search', 'enter'],
            'close_button': ['close', '×', 'x'],
            'minimize': ['minimize', 'min'],
            'maximize': ['maximize', 'max'],
            'play_button': ['play', '▶', 'start'],
            'pause_button': ['pause', '⏸', 'stop']
        }
    
    def detect_elements_adaptive(self, task_type: str = None, query: str = "", 
                                target_app: str = None, force_refresh: bool = False) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """
        Adaptively detect elements using the most efficient method for the task.
        """
        current_time = time.time()
        
        # Determine detection mode based on task and context
        detection_mode = self._determine_detection_mode(task_type, query, force_refresh, current_time)
        
        if detection_mode == DetectionMode.CACHED:
            return self._get_cached_elements()
        elif detection_mode == DetectionMode.FOCUSED:
            return self._get_focused_elements()
        elif detection_mode == DetectionMode.FAST:
            return self._get_fast_elements(task_type, query, target_app)
        else:  # SMART
            return self._get_intelligent_elements(task_type, query, target_app)
    
    def _determine_detection_mode(self, task_type: str, query: str, force_refresh: bool, current_time: float) -> DetectionMode:
        """Determine the most efficient detection mode for the task."""
        
        # Force refresh overrides everything
        if force_refresh:
            return DetectionMode.SMART
        
        # Check if we have recent cached data
        if current_time - self.last_refresh_time < 5.0 and not force_refresh:
            if self._has_recent_cache():
                return DetectionMode.CACHED
        
        # Determine based on task complexity
        query_lower = query.lower()
        
        # Fast detection for simple, common actions
        if self._is_simple_action(query_lower, task_type):
            return DetectionMode.FAST
        
        # Focused detection for typing tasks
        if task_type == TaskType.TEXT_INPUT or any(word in query_lower for word in ['type', 'enter', 'input']):
            return DetectionMode.FOCUSED
        
        # Smart detection for complex tasks
        if self._is_complex_task(query_lower, task_type):
            return DetectionMode.SMART
        
        # Default to fast for unknown tasks
        return DetectionMode.FAST
    
    def _is_simple_action(self, query_lower: str, task_type: str) -> bool:
        """Check if this is a simple action that can use fast detection."""
        simple_actions = [
            'new tab', 'close tab', 'refresh', 'back', 'forward',
            'minimize', 'maximize', 'close window', 'open new tab',
            'click new tab', 'press new tab'
        ]
        
        return any(action in query_lower for action in simple_actions)
    
    def _is_complex_task(self, query_lower: str, task_type: str) -> bool:
        """Check if this is a complex task requiring intelligent detection."""
        complex_indicators = [
            'find', 'search', 'locate', 'identify', 'detect',
            'first video', 'specific', 'particular', 'exact',
            'form', 'fill out', 'submit', 'navigate to'
        ]
        
        return any(indicator in query_lower for indicator in complex_indicators)
    
    def _has_recent_cache(self) -> bool:
        """Check if we have recent cached data."""
        return len(self.coordinate_cache) > 0 or len(self.element_cache) > 0
    
    def _get_cached_elements(self) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """Get elements from cache if available."""
        current_time = time.time()
        
        # Clean expired cache
        self._clean_expired_cache(current_time)
        
        if self.element_cache:
            interactive = self.element_cache.get('interactive', [])
            informative = self.element_cache.get('informative', [])
            scrollable = self.element_cache.get('scrollable', [])
            return interactive, informative, scrollable
        
        # Fallback to fast detection if no cache
        return self._get_fast_elements()
    
    def _get_focused_elements(self) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """Get only focused elements for typing tasks."""
        try:
            focused_control = GetFocusedControl()
            if not focused_control:
                return [], [], []
            
            # Create focused element node
            focused_node = self._create_element_from_control(focused_control, "Focused Element")
            if focused_node:
                return [focused_node], [], []
            
            return [], [], []
        except:
            return [], [], []
    
    def _get_fast_elements(self, task_type: str = None, query: str = "", target_app: str = None) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """Get elements using fast, direct detection methods."""
        interactive_nodes = []
        informative_nodes = []
        scrollable_nodes = []
        
        try:
            # Get focused control first (most important for typing)
            focused_control = GetFocusedControl()
            if focused_control:
                focused_node = self._create_element_from_control(focused_control, "Focused Element")
                if focused_node:
                    interactive_nodes.append(focused_node)
            
            # Get common elements quickly
            common_elements = self._detect_common_elements(query)
            interactive_nodes.extend(common_elements)
            
            # Limit results for performance
            interactive_nodes = interactive_nodes[:10]
            
            # Cache the results
            self._cache_elements(interactive_nodes, informative_nodes, scrollable_nodes)
            
        except Exception as e:
            print(f"Fast detection failed: {e}")
            # Fallback to basic detection
            return self._get_basic_elements()
        
        return interactive_nodes, informative_nodes, scrollable_nodes
    
    def _get_intelligent_elements(self, task_type: str, query: str, target_app: str) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """Get elements using intelligent detection."""
        try:
            result = self.intelligent_detector.detect_elements(
                task_type=task_type,
                query=query,
                target_app=target_app
            )
            
            # Extract the three lists from the result
            if hasattr(result, 'interactive_nodes'):
                # It's a TreeState object
                interactive_nodes = result.interactive_nodes
                informative_nodes = result.informative_nodes
                scrollable_nodes = result.scrollable_nodes
            else:
                # It's already a tuple of three lists
                interactive_nodes, informative_nodes, scrollable_nodes = result
            
            # Cache the results
            self._cache_elements(interactive_nodes, informative_nodes, scrollable_nodes)
            self.last_refresh_time = time.time()
            
            return interactive_nodes, informative_nodes, scrollable_nodes
        except Exception as e:
            print(f"Intelligent detection failed: {e}")
            return self._get_fast_elements(task_type, query, target_app)
    
    def _detect_common_elements(self, query: str) -> List[TreeElementNode]:
        """Detect common UI elements quickly."""
        elements = []
        query_lower = query.lower()
        
        try:
            # Get root control
            root = GetRootControl()
            
            # Look for common patterns
            for pattern_name, keywords in self.common_patterns.items():
                if any(keyword in query_lower for keyword in keywords):
                    element = self._find_element_by_pattern(root, pattern_name)
                    if element:
                        elements.append(element)
            
            # Always include focused element if available
            focused_element = self._get_focused_element()
            if focused_element and focused_element not in elements:
                elements.insert(0, focused_element)
                
        except Exception as e:
            print(f"Common element detection failed: {e}")
        
        return elements
    
    def _find_element_by_pattern(self, root: Control, pattern_name: str) -> Optional[TreeElementNode]:
        """Find element by common pattern."""
        try:
            if pattern_name == 'new_tab':
                return self._find_new_tab_button(root)
            elif pattern_name == 'address_bar':
                return self._find_address_bar(root)
            elif pattern_name == 'search_box':
                return self._find_search_box(root)
            elif pattern_name == 'play_button':
                return self._find_play_button(root)
            # Add more patterns as needed
        except:
            pass
        return None
    
    def _find_new_tab_button(self, root: Control) -> Optional[TreeElementNode]:
        """Find new tab button quickly."""
        try:
            # Look for common new tab button patterns
            for child in root.GetChildren():
                if child.ControlType == ControlType.ButtonControl:
                    name = child.Name.lower()
                    if any(keyword in name for keyword in ['new tab', 'newtab', '+', 'add']):
                        return self._create_element_from_control(child, "New Tab Button")
        except:
            pass
        return None
    
    def _find_address_bar(self, root: Control) -> Optional[TreeElementNode]:
        """Find address bar quickly."""
        try:
            # Look for focused text control (usually address bar)
            focused = GetFocusedControl()
            if focused and focused.ControlType in [ControlType.EditControl, ControlType.TextControl]:
                return self._create_element_from_control(focused, "Address Bar")
        except:
            pass
        return None
    
    def _find_search_box(self, root: Control) -> Optional[TreeElementNode]:
        """Find search box quickly."""
        try:
            for child in root.GetChildren():
                if child.ControlType == ControlType.EditControl:
                    name = child.Name.lower()
                    if any(keyword in name for keyword in ['search', 'find', 'query']):
                        return self._create_element_from_control(child, "Search Box")
        except:
            pass
        return None
    
    def _find_play_button(self, root: Control) -> Optional[TreeElementNode]:
        """Find play button quickly."""
        try:
            for child in root.GetChildren():
                if child.ControlType == ControlType.ButtonControl:
                    name = child.Name.lower()
                    if any(keyword in name for keyword in ['play', '▶', 'start']):
                        return self._create_element_from_control(child, "Play Button")
        except:
            pass
        return None
    
    def _get_focused_element(self) -> Optional[TreeElementNode]:
        """Get currently focused element."""
        try:
            focused = GetFocusedControl()
            if focused:
                return self._create_element_from_control(focused, "Focused Element")
        except:
            pass
        return None
    
    def _create_element_from_control(self, control: Control, name: str) -> Optional[TreeElementNode]:
        """Create TreeElementNode from Control."""
        try:
            from windows_use.tree.views import Center, BoundingBox
            
            rect = control.BoundingRectangle
            if rect.isempty():
                return None
            
            center = Center(x=rect.left + rect.width() // 2, y=rect.top + rect.height() // 2)
            bounding_box = BoundingBox(
                left=rect.left,
                top=rect.top,
                right=rect.right,
                bottom=rect.bottom
            )
            
            return TreeElementNode(
                name=name,
                control_type=control.ControlTypeName,
                center=center,
                bounding_box=bounding_box,
                is_enabled=getattr(control, 'IsEnabled', True),
                is_visible=getattr(control, 'IsVisible', True),
                handle=control.NativeWindowHandle,
                priority=3  # High priority for focused elements
            )
        except:
            return None
    
    def _get_basic_elements(self) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """Fallback to basic element detection."""
        try:
            from windows_use.tree.service import Tree
            tree = Tree(self.desktop)
            return tree.get_state()
        except:
            return [], [], []
    
    def _cache_elements(self, interactive: List[TreeElementNode], 
                       informative: List[TextElementNode], 
                       scrollable: List[ScrollElementNode]):
        """Cache elements for future use."""
        current_time = time.time()
        
        self.element_cache = {
            'interactive': interactive,
            'informative': informative,
            'scrollable': scrollable,
            'timestamp': current_time
        }
    
    def _clean_expired_cache(self, current_time: float):
        """Clean expired cache entries."""
        if 'timestamp' in self.element_cache:
            if current_time - self.element_cache['timestamp'] > self.cache_timeout:
                self.element_cache.clear()
    
    def clear_cache(self):
        """Clear all cached data."""
        self.coordinate_cache.clear()
        self.element_cache.clear()
        self.last_refresh_time = 0
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection performance statistics."""
        return {
            'cache_size': len(self.element_cache),
            'last_refresh': self.last_refresh_time,
            'cache_timeout': self.cache_timeout
        }
