"""
Intelligent Element Detection System

This module provides smart, context-aware element detection that focuses on
the most likely targets based on user intent and UI state.
"""

from uiautomation import Control, ControlType, GetFocusedControl
from windows_use.tree.views import TreeElementNode, TextElementNode, ScrollElementNode, Center, BoundingBox
from typing import List, Tuple, Optional, Dict, Any
import re
from enum import Enum

class TaskType(Enum):
    TEXT_INPUT = "text_input"
    BUTTON_CLICK = "button_click"
    NAVIGATION = "navigation"
    READING = "reading"
    SCROLLING = "scrolling"
    TAB_OPERATION = "tab_operation"
    FORM_FILLING = "form_filling"
    SEARCH = "search"

class ElementPriority(Enum):
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    IGNORE = 0

class IntelligentDetector:
    """
    Smart element detector that uses context and UI state to find the most relevant elements.
    """
    
    def __init__(self, desktop):
        self.desktop = desktop
        self.focused_control = None
        self.task_context = {}
        
    def detect_elements(self, task_type: TaskType, query: str = "", target_app: str = None) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """
        Intelligently detect elements based on task type and context.
        """
        # Get focused control first (most important)
        self.focused_control = self._get_focused_control()
        
        # Determine context from query
        self.task_context = self._analyze_query_context(query)
        
        # Get base elements
        interactive_nodes, informative_nodes, scrollable_nodes = self._get_base_elements(target_app)
        
        # Apply intelligent filtering and prioritization
        if task_type == TaskType.TEXT_INPUT:
            interactive_nodes = self._prioritize_text_inputs(interactive_nodes)
        elif task_type == TaskType.BUTTON_CLICK:
            interactive_nodes = self._prioritize_buttons(interactive_nodes)
        elif task_type == TaskType.TAB_OPERATION:
            interactive_nodes = self._prioritize_tabs(interactive_nodes)
        elif task_type == TaskType.READING:
            informative_nodes = self._prioritize_readable_content(informative_nodes)
        elif task_type == TaskType.SEARCH:
            interactive_nodes = self._prioritize_search_elements(interactive_nodes)
        
        # Limit results to most relevant elements
        interactive_nodes = self._limit_results(interactive_nodes, max_elements=20)
        informative_nodes = self._limit_results(informative_nodes, max_elements=15)
        scrollable_nodes = self._limit_results(scrollable_nodes, max_elements=10)
        
        return interactive_nodes, informative_nodes, scrollable_nodes
    
    def _get_focused_control(self) -> Optional[Control]:
        """Get the currently focused control."""
        try:
            return GetFocusedControl()
        except:
            return None
    
    def _analyze_query_context(self, query: str) -> Dict[str, Any]:
        """Analyze the query to understand user intent."""
        context = {
            'keywords': [],
            'action_type': None,
            'target_element': None,
            'urgency': 'normal'
        }
        
        query_lower = query.lower()
        
        # Extract keywords
        keywords = re.findall(r'\b\w+\b', query_lower)
        context['keywords'] = keywords
        
        # Determine action type
        if any(word in query_lower for word in ['type', 'enter', 'input', 'write', 'fill']):
            context['action_type'] = 'text_input'
        elif any(word in query_lower for word in ['click', 'press', 'tap', 'select']):
            context['action_type'] = 'button_click'
        elif any(word in query_lower for word in ['find', 'search', 'look']):
            context['action_type'] = 'search'
        elif any(word in query_lower for word in ['read', 'show', 'list', 'display']):
            context['action_type'] = 'reading'
        elif any(word in query_lower for word in ['tab', 'browser', 'window']):
            context['action_type'] = 'tab_operation'
        
        # Determine urgency
        if any(word in query_lower for word in ['urgent', 'quick', 'fast', 'now']):
            context['urgency'] = 'high'
        
        return context
    
    def _get_base_elements(self, target_app: str = None):
        """Get base elements using existing tree service."""
        from windows_use.tree.service import Tree
        tree = Tree(self.desktop)
        
        if target_app:
            return tree.get_precise_state(target_app)
        else:
            return tree.get_state()
    
    def _prioritize_text_inputs(self, elements: List[TreeElementNode]) -> List[TreeElementNode]:
        """Prioritize text input elements based on focus and context."""
        prioritized = []
        
        for element in elements:
            if not self._is_text_input(element):
                continue
                
            priority = ElementPriority.LOW
            
            # Check if it's the focused element
            if self._is_focused_element(element):
                priority = ElementPriority.HIGH
            # Check if it's enabled and visible
            elif self._is_element_ready(element):
                priority = ElementPriority.MEDIUM
            # Check for placeholder text or labels
            elif self._has_relevant_placeholder(element):
                priority = ElementPriority.MEDIUM
            
            if priority != ElementPriority.IGNORE:
                element.priority = priority.value
                prioritized.append(element)
        
        # Sort by priority (highest first)
        prioritized.sort(key=lambda x: getattr(x, 'priority', 0), reverse=True)
        return prioritized
    
    def _prioritize_buttons(self, elements: List[TreeElementNode]) -> List[TreeElementNode]:
        """Prioritize button elements based on prominence and state."""
        prioritized = []
        
        for element in elements:
            if not self._is_button(element):
                continue
                
            priority = ElementPriority.LOW
            
            # Check if it's enabled
            if not self._is_element_enabled(element):
                continue
                
            # Check for primary action buttons
            if self._is_primary_button(element):
                priority = ElementPriority.HIGH
            # Check if it's currently focused or hovered
            elif self._is_focused_element(element):
                priority = ElementPriority.HIGH
            # Check for common action words
            elif self._has_action_text(element):
                priority = ElementPriority.MEDIUM
            
            if priority != ElementPriority.IGNORE:
                element.priority = priority.value
                prioritized.append(element)
        
        prioritized.sort(key=lambda x: getattr(x, 'priority', 0), reverse=True)
        return prioritized
    
    def _prioritize_tabs(self, elements: List[TreeElementNode]) -> List[TreeElementNode]:
        """Prioritize tab-related elements."""
        prioritized = []
        
        for element in elements:
            if not self._is_tab_element(element):
                continue
                
            priority = ElementPriority.LOW
            
            # Check if it's the active tab
            if self._is_active_tab(element):
                priority = ElementPriority.HIGH
            # Check if it's visible and clickable
            elif self._is_element_ready(element):
                priority = ElementPriority.MEDIUM
            
            if priority != ElementPriority.IGNORE:
                element.priority = priority.value
                prioritized.append(element)
        
        prioritized.sort(key=lambda x: getattr(x, 'priority', 0), reverse=True)
        return prioritized
    
    def _prioritize_readable_content(self, elements: List[TextElementNode]) -> List[TextElementNode]:
        """Prioritize readable content elements."""
        prioritized = []
        
        for element in elements:
            if not self._is_readable_content(element):
                continue
                
            priority = ElementPriority.LOW
            
            # Check if it's currently visible
            if self._is_element_visible(element):
                priority = ElementPriority.MEDIUM
            # Check for important content indicators
            if self._has_important_content(element):
                priority = ElementPriority.HIGH
            
            if priority != ElementPriority.IGNORE:
                element.priority = priority.value
                prioritized.append(element)
        
        prioritized.sort(key=lambda x: getattr(x, 'priority', 0), reverse=True)
        return prioritized
    
    def _prioritize_search_elements(self, elements: List[TreeElementNode]) -> List[TreeElementNode]:
        """Prioritize search-related elements."""
        prioritized = []
        
        for element in elements:
            if not self._is_search_element(element):
                continue
                
            priority = ElementPriority.LOW
            
            # Check if it's focused (user is about to search)
            if self._is_focused_element(element):
                priority = ElementPriority.HIGH
            # Check for search indicators
            elif self._has_search_indicators(element):
                priority = ElementPriority.MEDIUM
            
            if priority != ElementPriority.IGNORE:
                element.priority = priority.value
                prioritized.append(element)
        
        prioritized.sort(key=lambda x: getattr(x, 'priority', 0), reverse=True)
        return prioritized
    
    # Helper methods for element classification
    def _is_text_input(self, element: TreeElementNode) -> bool:
        """Check if element is a text input."""
        return (hasattr(element, 'control_type') and 
                element.control_type in ['EditControl', 'TextControl'] and
                hasattr(element, 'is_enabled') and element.is_enabled)
    
    def _is_button(self, element: TreeElementNode) -> bool:
        """Check if element is a button."""
        return (hasattr(element, 'control_type') and 
                element.control_type in ['ButtonControl', 'HyperlinkControl'])
    
    def _is_tab_element(self, element: TreeElementNode) -> bool:
        """Check if element is tab-related."""
        if not hasattr(element, 'name'):
            return False
        name_lower = element.name.lower()
        return any(keyword in name_lower for keyword in ['tab', 'browser', 'window', 'page'])
    
    def _is_readable_content(self, element: TextElementNode) -> bool:
        """Check if element contains readable content."""
        if not hasattr(element, 'text') or not element.text:
            return False
        # Filter out very short or non-informative text
        return len(element.text.strip()) > 3 and not element.text.strip().isdigit()
    
    def _is_search_element(self, element: TreeElementNode) -> bool:
        """Check if element is search-related."""
        if not hasattr(element, 'name'):
            return False
        name_lower = element.name.lower()
        return any(keyword in name_lower for keyword in ['search', 'find', 'query', 'lookup'])
    
    # Helper methods for element state
    def _is_focused_element(self, element: TreeElementNode) -> bool:
        """Check if element is currently focused."""
        if not self.focused_control:
            return False
        return (hasattr(element, 'handle') and 
                element.handle == self.focused_control.NativeWindowHandle)
    
    def _is_element_ready(self, element: TreeElementNode) -> bool:
        """Check if element is ready for interaction."""
        return (hasattr(element, 'is_enabled') and element.is_enabled and
                hasattr(element, 'is_visible') and element.is_visible)
    
    def _is_element_enabled(self, element: TreeElementNode) -> bool:
        """Check if element is enabled."""
        return hasattr(element, 'is_enabled') and element.is_enabled
    
    def _is_element_visible(self, element: TreeElementNode) -> bool:
        """Check if element is visible."""
        return hasattr(element, 'is_visible') and element.is_visible
    
    def _is_active_tab(self, element: TreeElementNode) -> bool:
        """Check if element is the active tab."""
        # This would need to be implemented based on specific UI patterns
        # For now, check if it's focused or has active styling
        return self._is_focused_element(element)
    
    def _has_relevant_placeholder(self, element: TreeElementNode) -> bool:
        """Check if element has relevant placeholder text."""
        if not hasattr(element, 'name'):
            return False
        name_lower = element.name.lower()
        return any(keyword in name_lower for keyword in ['enter', 'type', 'input', 'search'])
    
    def _is_primary_button(self, element: TreeElementNode) -> bool:
        """Check if element is a primary action button."""
        if not hasattr(element, 'name'):
            return False
        name_lower = element.name.lower()
        primary_actions = ['submit', 'save', 'continue', 'next', 'ok', 'confirm', 'apply']
        return any(action in name_lower for action in primary_actions)
    
    def _has_action_text(self, element: TreeElementNode) -> bool:
        """Check if element has action-related text."""
        if not hasattr(element, 'name'):
            return False
        name_lower = element.name.lower()
        action_words = ['click', 'press', 'select', 'choose', 'open', 'close', 'start', 'stop']
        return any(word in name_lower for word in action_words)
    
    def _has_important_content(self, element: TextElementNode) -> bool:
        """Check if element contains important content."""
        if not hasattr(element, 'text'):
            return False
        text_lower = element.text.lower()
        important_indicators = ['error', 'warning', 'success', 'important', 'notice', 'alert']
        return any(indicator in text_lower for indicator in important_indicators)
    
    def _has_search_indicators(self, element: TreeElementNode) -> bool:
        """Check if element has search-related indicators."""
        if not hasattr(element, 'name'):
            return False
        name_lower = element.name.lower()
        search_indicators = ['search', 'find', 'query', 'lookup', 'filter']
        return any(indicator in name_lower for indicator in search_indicators)
    
    def _limit_results(self, elements: List, max_elements: int) -> List:
        """Limit results to the most relevant elements."""
        return elements[:max_elements]
