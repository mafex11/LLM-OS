"""
Precise Element Detection for Specific Applications

This module provides more precise element detection by focusing on specific application windows
and their child elements, rather than scanning the entire desktop.
"""

from uiautomation import Control, GetRootControl, ControlType, ControlFromHandle
from windows_use.tree.views import TreeElementNode, TextElementNode, ScrollElementNode, Center, BoundingBox
from windows_use.tree.utils import random_point_within_bounding_box
from typing import List, Tuple, Optional
import time


class PreciseElementDetector:
    """
    A more precise element detector that focuses on specific application windows
    and their child elements.
    """
    
    def __init__(self, desktop):
        self.desktop = desktop
    
    def get_calculator_elements(self) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """
        Get elements specifically from the Calculator application.
        """
        calculator_window = self._find_calculator_window()
        if not calculator_window:
            return [], [], []
        
        return self._get_elements_from_window(calculator_window, "Calculator")
    
    def get_elements_from_app(self, app_name: str) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """
        Get elements from a specific application by name.
        """
        app_window = self._find_app_window(app_name)
        if not app_window:
            return [], [], []
        
        return self._get_elements_from_window(app_window, app_name)
    
    def _find_calculator_window(self) -> Optional[Control]:
        """
        Find the Calculator application window specifically.
        """
        root = GetRootControl()
        
        # Look for calculator windows with specific characteristics
        for window in root.GetChildren():
            if self._is_calculator_window(window):
                return window
        
        return None
    
    def _find_app_window(self, app_name: str) -> Optional[Control]:
        """
        Find a specific application window by name.
        """
        root = GetRootControl()
        app_name_lower = app_name.lower()
        
        for window in root.GetChildren():
            if (window.Name and app_name_lower in window.Name.lower()) or \
               (window.ClassName and app_name_lower in window.ClassName.lower()):
                return window
        
        return None
    
    def _is_calculator_window(self, window: Control) -> bool:
        """
        Check if a window is the Calculator application.
        """
        # Check for calculator-specific characteristics
        name = window.Name.lower() if window.Name else ""
        class_name = window.ClassName.lower() if window.ClassName else ""
        
        # Calculator window identifiers
        calculator_indicators = [
            "calculator",
            "calc",
            "windows calculator",
            "microsoft calculator"
        ]
        
        # Check if any calculator indicator is in the name or class
        for indicator in calculator_indicators:
            if indicator in name or indicator in class_name:
                return True
        
        # Additional check: look for calculator-specific child elements
        try:
            children = window.GetChildren()
            for child in children:
                if child.ControlType == ControlType.TextControl:
                    # Calculator typically has a display area
                    if child.Name and any(char.isdigit() for char in child.Name):
                        return True
        except:
            pass
        
        return False
    
    def _get_elements_from_window(self, window: Control, app_name: str) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """
        Get all interactive, informative, and scrollable elements from a specific window.
        """
        interactive_nodes = []
        informative_nodes = []
        scrollable_nodes = []
        
        try:
            # Get all child elements from the window
            self._traverse_window_elements(window, app_name, interactive_nodes, informative_nodes, scrollable_nodes)
        except Exception as e:
            print(f"Error traversing window elements: {e}")
        
        return interactive_nodes, informative_nodes, scrollable_nodes
    
    def _traverse_window_elements(self, node: Control, app_name: str, 
                                interactive_nodes: List[TreeElementNode], 
                                informative_nodes: List[TextElementNode], 
                                scrollable_nodes: List[ScrollElementNode]):
        """
        Recursively traverse window elements to find interactive, informative, and scrollable elements.
        """
        try:
            # Check if element is visible and interactive
            if self._is_element_interactive(node):
                element_node = self._create_interactive_node(node, app_name)
                if element_node:
                    interactive_nodes.append(element_node)
            
            # Check if element is informative (text)
            elif self._is_element_informative(node):
                text_node = self._create_informative_node(node, app_name)
                if text_node:
                    informative_nodes.append(text_node)
            
            # Check if element is scrollable
            elif self._is_element_scrollable(node):
                scroll_node = self._create_scrollable_node(node, app_name)
                if scroll_node:
                    scrollable_nodes.append(scroll_node)
            
            # Recursively check children
            for child in node.GetChildren():
                self._traverse_window_elements(child, app_name, interactive_nodes, informative_nodes, scrollable_nodes)
                
        except Exception as e:
            # Skip elements that can't be processed
            pass
    
    def _is_element_interactive(self, node: Control) -> bool:
        """
        Check if an element is interactive (clickable, typeable, etc.).
        """
        try:
            if not node.IsControlElement:
                return False
            
            box = node.BoundingRectangle
            if box.isempty():
                return False
            
            # Check if element is visible and has reasonable size
            if box.width() < 5 or box.height() < 5:
                return False
            
            # Check for interactive control types
            interactive_types = [
                ControlType.ButtonControl,
                ControlType.EditControl,
                ControlType.ComboBoxControl,
                ControlType.ListControl,
                ControlType.ListItemControl,
                ControlType.MenuControl,
                ControlType.MenuItemControl,
                ControlType.HyperlinkControl,
                ControlType.CheckBoxControl,
                ControlType.RadioButtonControl,
                ControlType.SliderControl,
                ControlType.TabControl,
                ControlType.TabItemControl,
                ControlType.ToggleControl
            ]
            
            return node.ControlType in interactive_types
            
        except:
            return False
    
    def _is_element_informative(self, node: Control) -> bool:
        """
        Check if an element is informative (displays text).
        """
        try:
            if not node.IsControlElement:
                return False
            
            box = node.BoundingRectangle
            if box.isempty():
                return False
            
            # Check for text control types
            text_types = [
                ControlType.TextControl,
                ControlType.StaticControl,
                ControlType.LabelControl
            ]
            
            return node.ControlType in text_types and node.Name and node.Name.strip()
            
        except:
            return False
    
    def _is_element_scrollable(self, node: Control) -> bool:
        """
        Check if an element is scrollable.
        """
        try:
            if not node.IsControlElement:
                return False
            
            # Try to get scroll pattern
            scroll_pattern = node.GetScrollPattern()
            return scroll_pattern is not None
            
        except:
            return False
    
    def _create_interactive_node(self, node: Control, app_name: str) -> Optional[TreeElementNode]:
        """
        Create an interactive element node.
        """
        try:
            box = node.BoundingRectangle
            
            # Use center coordinates for better accuracy
            x, y = box.xcenter(), box.ycenter()
            center = Center(x=x, y=y)
            
            return TreeElementNode(
                name=node.Name.strip() if node.Name else "",
                control_type=node.LocalizedControlType.title(),
                shortcut=node.AcceleratorKey or "",
                bounding_box=BoundingBox(
                    left=box.left,
                    top=box.top,
                    right=box.right,
                    bottom=box.bottom,
                    width=box.width(),
                    height=box.height()
                ),
                center=center,
                app_name=app_name
            )
        except:
            return None
    
    def _create_informative_node(self, node: Control, app_name: str) -> Optional[TextElementNode]:
        """
        Create an informative element node.
        """
        try:
            box = node.BoundingRectangle
            x, y = box.xcenter(), box.ycenter()
            center = Center(x=x, y=y)
            
            return TextElementNode(
                name=node.Name.strip() if node.Name else "",
                control_type=node.LocalizedControlType.title(),
                bounding_box=BoundingBox(
                    left=box.left,
                    top=box.top,
                    right=box.right,
                    bottom=box.bottom,
                    width=box.width(),
                    height=box.height()
                ),
                center=center,
                app_name=app_name
            )
        except:
            return None
    
    def _create_scrollable_node(self, node: Control, app_name: str) -> Optional[ScrollElementNode]:
        """
        Create a scrollable element node.
        """
        try:
            box = node.BoundingRectangle
            x, y = box.xcenter(), box.ycenter()
            center = Center(x=x, y=y)
            
            scroll_pattern = node.GetScrollPattern()
            horizontal_scrollable = scroll_pattern.HorizontallyScrollable if scroll_pattern else False
            vertical_scrollable = scroll_pattern.VerticallyScrollable if scroll_pattern else False
            
            return ScrollElementNode(
                name=node.Name.strip() if node.Name else "",
                control_type=node.LocalizedControlType.title(),
                bounding_box=BoundingBox(
                    left=box.left,
                    top=box.top,
                    right=box.right,
                    bottom=box.bottom,
                    width=box.width(),
                    height=box.height()
                ),
                center=center,
                app_name=app_name,
                horizontal_scrollable=horizontal_scrollable,
                vertical_scrollable=vertical_scrollable
            )
        except:
            return None
