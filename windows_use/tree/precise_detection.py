"""
Precise Element Detection for Application Windows

This module focuses on retrieving high-confidence UI metadata for a specific
window. It ensures the window is ready for interaction (visible, restored)
before walking the accessibility tree and returning interactive, informative,
and scrollable nodes with screen-relative coordinates.
"""

from uiautomation import Control, ControlType
from windows_use.tree.views import (
    TreeElementNode,
    TextElementNode,
    ScrollElementNode,
    Center,
    BoundingBox,
)
from typing import Callable, List, Tuple, Optional
from collections import deque
import time


class PreciseElementDetector:
    """
    A detector that extracts detailed UI metadata from a specific application window.
    """

    def __init__(self, desktop):
        self.desktop = desktop

    def get_elements_for_window(
        self, window: Control | None, app_name: str | None = None
    ) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """
        Collect elements for a specific top-level window.

        Args:
            window: The top-level window control to inspect.
            app_name: Optional friendly name override for metadata.

        Returns:
            Tuple of (interactive_nodes, informative_nodes, scrollable_nodes)
        """
        if window is None:
            return [], [], []

        resolved_name = (app_name or window.Name or window.ClassName or "Window").strip()

        # OPTIMIZATION: For browsers, precise detection is too slow (20-40 seconds)
        # Return empty to force fallback to faster generic traversal
        browser_keywords = ['chrome', 'firefox', 'edge', 'opera', 'brave', 'vivaldi']
        if any(keyword in resolved_name.lower() for keyword in browser_keywords):
            return [], [], []  # Force fallback to faster method

        # Ensure the window is in a stable, visible state before traversing.
        self._prepare_window(window)

        interactive, informative, scrollable = self._get_elements_from_window(
            window, resolved_name or "Window"
        )

        self._augment_browser_nodes(
            window,
            resolved_name,
            interactive,
            informative,
            scrollable,
        )

        # If nothing was detected (some apps expose controls differently), fall back to
        # returning an empty set so the caller can decide how to proceed.
        return interactive, informative, scrollable

    def _prepare_window(self, window: Control) -> None:
        """
        Best-effort attempt to make sure the window is visible and restored.
        """
        try:
            from uiautomation import IsIconic, ShowWindow

            hwnd = window.NativeWindowHandle
            if IsIconic(hwnd):
                ShowWindow(hwnd, cmdShow=9)  # SW_RESTORE
                time.sleep(0.1)  # Optimized: reduced from 300ms to 100ms
        except Exception:
            # If we cannot restore the window, continue; traversal may still succeed.
            pass

    def _get_elements_from_window(
        self, window: Control, app_name: str
    ) -> Tuple[List[TreeElementNode], List[TextElementNode], List[ScrollElementNode]]:
        """
        Get all interactive, informative, and scrollable elements from a specific window.
        CRITICAL: Only includes elements that are actually within the window bounds and belong to the same process.
        """
        interactive_nodes = []
        informative_nodes = []
        scrollable_nodes = []
        
        try:
            # Get window bounds to validate elements are actually within this window
            window_box = window.BoundingRectangle
            if window_box.isempty():
                print(f"Warning: {app_name} window has empty bounding rectangle")
                return [], [], []
            
            window_left = window_box.left
            window_top = window_box.top
            window_right = window_box.right
            window_bottom = window_box.bottom
            
            # Get window process ID to ensure elements belong to this window
            self._traverse_window_elements(
                window,
                app_name,
                interactive_nodes,
                informative_nodes,
                scrollable_nodes,
                window_bounds=(window_left, window_top, window_right, window_bottom),
                window_handle=window.NativeWindowHandle,
            )
        except Exception as e:
            print(f"Error traversing window elements: {e}")
        
        return interactive_nodes, informative_nodes, scrollable_nodes

    def _traverse_window_elements(
        self,
        node: Control,
        app_name: str,
        interactive_nodes: List[TreeElementNode],
        informative_nodes: List[TextElementNode],
        scrollable_nodes: List[ScrollElementNode],
        window_bounds: Tuple[int, int, int, int] = None,
        window_handle: int | None = None,
    ):
        """
        Recursively traverse window elements to find interactive, informative, and scrollable elements.
        Only includes elements that are within the window bounds and belong to the same process.
        """
        try:
            element_window = None
            if window_handle is not None:
                try:
                    element_window = self.desktop.get_window_element_from_element(node)
                except Exception:
                    element_window = None

                if element_window and element_window.NativeWindowHandle != window_handle:
                    for child in node.GetChildren():
                        self._traverse_window_elements(
                            child,
                            app_name,
                            interactive_nodes,
                            informative_nodes,
                            scrollable_nodes,
                            window_bounds=window_bounds,
                            window_handle=window_handle,
                        )
                    return

            element_box = node.BoundingRectangle
            if not element_box.isempty() and window_bounds:
                window_left, window_top, window_right, window_bottom = window_bounds
                if (
                    element_box.right < window_left - 10
                    or element_box.left > window_right + 10
                    or element_box.bottom < window_top - 10
                    or element_box.top > window_bottom + 10
                ):
                    for child in node.GetChildren():
                        self._traverse_window_elements(
                            child,
                            app_name,
                            interactive_nodes,
                            informative_nodes,
                            scrollable_nodes,
                            window_bounds=window_bounds,
                            window_handle=window_handle,
                        )
                    return

                if self._is_element_interactive(node):
                    element_node = self._create_interactive_node(node, app_name)
                    if element_node:
                        self._append_unique_interactive(interactive_nodes, element_node)
                elif self._is_element_informative(node):
                    text_node = self._create_informative_node(node, app_name)
                    if text_node:
                        self._append_unique_informative(informative_nodes, text_node)
                elif self._is_element_scrollable(node):
                    scroll_node = self._create_scrollable_node(node, app_name)
                    if scroll_node:
                        self._append_unique_scrollable(scrollable_nodes, scroll_node)

            for child in node.GetChildren():
                self._traverse_window_elements(
                    child,
                    app_name,
                    interactive_nodes,
                    informative_nodes,
                    scrollable_nodes,
                    window_bounds=window_bounds,
                    window_handle=window_handle,
                )
                
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
                ControlType.ToggleControl,
            ]

            if node.ControlType in interactive_types:
                return True

            extended_types = (
                ControlType.PaneControl,
                ControlType.CustomControl,
                ControlType.DocumentControl,
                ControlType.ToolBarControl,
                ControlType.WindowControl,
            )

            if node.ControlType in extended_types:
                try:
                    if node.IsKeyboardFocusable:
                        return True
                except Exception:
                    pass
                try:
                    legacy = node.GetLegacyIAccessiblePattern()
                    if legacy:
                        default_action = getattr(legacy, "DefaultAction", "")
                        if isinstance(default_action, str) and default_action.strip():
                            return True
                except Exception:
                    pass

                automation_id = self._get_automation_id(node)
                if automation_id and any(keyword in automation_id for keyword in ("omnibox", "urlbar", "address")):
                    return True

            return False

        except Exception:
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
            name = self._extract_node_name(node)

            x, y = box.xcenter(), box.ycenter()
            center = Center(x=x, y=y)

            return TreeElementNode(
                name=name,
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
            name = self._extract_node_name(node)

            return TextElementNode(
                name=name,
                app_name=app_name,
                control_type=node.LocalizedControlType.title(),
                bounding_box=BoundingBox(
                    left=box.left,
                    top=box.top,
                    right=box.right,
                    bottom=box.bottom,
                    width=box.width(),
                    height=box.height()
                ),
                center=center
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
            name = self._extract_node_name(node)

            scroll_pattern = node.GetScrollPattern()
            horizontal_scrollable = scroll_pattern.HorizontallyScrollable if scroll_pattern else False
            vertical_scrollable = scroll_pattern.VerticallyScrollable if scroll_pattern else False

            return ScrollElementNode(
                name=name,
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

    def _append_unique_interactive(
        self,
        nodes: List[TreeElementNode],
        node: Optional[TreeElementNode],
    ) -> None:
        if not node or not node.bounding_box:
            return

        for existing in nodes:
            if not existing.bounding_box:
                continue
            if self._boxes_close(existing.bounding_box, node.bounding_box):
                existing_type = (existing.control_type or "").lower()
                node_type = (node.control_type or "").lower()
                existing_name = (existing.name or "").lower()
                node_name = (node.name or "").lower()
                if existing_type == node_type and (not node_name or node_name == existing_name):
                    return
                if self._centers_close(existing.center, node.center):
                    if node_name == existing_name:
                        return
        nodes.append(node)

    def _append_unique_informative(
        self,
        nodes: List[TextElementNode],
        node: Optional[TextElementNode],
    ) -> None:
        if not node:
            return
        new_name = (node.name or "").lower()
        if not new_name:
            return
        for existing in nodes:
            if (existing.name or "").lower() == new_name and existing.app_name == node.app_name:
                return
        nodes.append(node)

    def _append_unique_scrollable(
        self,
        nodes: List[ScrollElementNode],
        node: Optional[ScrollElementNode],
    ) -> None:
        if not node or not node.bounding_box:
            return
        for existing in nodes:
            if not existing.bounding_box:
                continue
            if self._boxes_close(existing.bounding_box, node.bounding_box):
                return
        nodes.append(node)

    def _boxes_close(self, first: BoundingBox, second: BoundingBox, tolerance: int = 4) -> bool:
        return (
            abs(first.left - second.left) <= tolerance
            and abs(first.top - second.top) <= tolerance
            and abs(first.right - second.right) <= tolerance
            and abs(first.bottom - second.bottom) <= tolerance
        )

    def _centers_close(self, first: Center, second: Center, tolerance: int = 3) -> bool:
        return abs(first.x - second.x) <= tolerance and abs(first.y - second.y) <= tolerance

    def _extract_node_name(self, node: Control) -> str:
        for attr in ("Name", "AutomationId", "ClassName"):
            try:
                value = getattr(node, attr)
            except Exception:
                value = ""
            if value:
                value = value.strip()
                if value:
                    return value
        return ""

    def _get_automation_id(self, node: Control) -> str:
        try:
            automation_id = node.AutomationId
            if automation_id:
                return automation_id.strip().lower()
        except Exception:
            pass
        return ""

    def _safe_runtime_id(self, node: Control):
        try:
            runtime_id = node.GetRuntimeId()
            if runtime_id:
                if isinstance(runtime_id, (list, tuple)):
                    return tuple(runtime_id)
                return runtime_id
        except Exception:
            pass
        try:
            return (node.NativeWindowHandle, id(node))
        except Exception:
            return id(node)

    def _find_descendant(
        self,
        root: Control,
        predicate: Callable[[Control], bool],
        max_depth: int = 12,
    ) -> Optional[Control]:
        queue = deque([(root, 0)])
        visited = set()

        while queue:
            node, depth = queue.popleft()
            identifier = self._safe_runtime_id(node)
            if identifier in visited:
                continue
            visited.add(identifier)

            try:
                if predicate(node):
                    return node
            except Exception:
                pass

            if depth >= max_depth:
                continue

            try:
                children = node.GetChildren()
            except Exception:
                children = []

            for child in children:
                queue.append((child, depth + 1))

        return None

    def _matches_browser_address(self, node: Control) -> bool:
        try:
            if node.ControlType != ControlType.EditControl:
                return False
            name = (node.Name or "").strip().lower()
            automation_id = self._get_automation_id(node)
            if name and any(keyword in name for keyword in ("address", "search", "omnibox", "url")):
                return True
            if automation_id and any(keyword in automation_id for keyword in ("omnibox", "urlbar", "address")):
                return True
            return False
        except Exception:
            return False

    def _matches_named_button(self, node: Control, keywords: Tuple[str, ...]) -> bool:
        try:
            if node.ControlType != ControlType.ButtonControl:
                return False
            name = (node.Name or "").strip().lower()
            if name and any(keyword in name for keyword in keywords):
                return True
            automation_id = self._get_automation_id(node)
            if automation_id and any(keyword in automation_id for keyword in keywords):
                return True
            return False
        except Exception:
            return False

    def _matches_browser_tab(self, node: Control) -> bool:
        try:
            if node.ControlType not in (ControlType.TabItemControl, ControlType.ButtonControl):
                return False
            name = (node.Name or "").strip().lower()
            if name and "tab" in name:
                return True
            automation_id = self._get_automation_id(node)
            if automation_id and "tab" in automation_id:
                return True
            return False
        except Exception:
            return False

    def _augment_browser_nodes(
        self,
        window: Control,
        app_name: str,
        interactive_nodes: List[TreeElementNode],
        informative_nodes: List[TextElementNode],
        scrollable_nodes: List[ScrollElementNode],
    ) -> None:
        name_lower = (app_name or "").lower()
        if not any(browser in name_lower for browser in ("chrome", "edge", "firefox")):
            return

        # Ensure address bar is present
        if not any("address" in (node.name or "").lower() for node in interactive_nodes):
            address_control = self._find_descendant(
                window,
                self._matches_browser_address,
                max_depth=18,
            )
            if address_control:
                address_node = self._create_interactive_node(address_control, app_name)
                if address_node:
                    if not address_node.name:
                        address_node.name = "Address bar"
                    self._append_unique_interactive(interactive_nodes, address_node)

        # Ensure tab control is available
        if not any("tab" in (node.name or "").lower() for node in interactive_nodes):
            tab_control = self._find_descendant(
                window,
                self._matches_browser_tab,
                max_depth=18,
            )
            if tab_control:
                tab_node = self._create_interactive_node(tab_control, app_name)
                if tab_node:
                    self._append_unique_interactive(interactive_nodes, tab_node)

        # Core browser navigation buttons
        browser_buttons: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
            ("reload", ("reload", "refresh")),
            ("back", ("back",)),
            ("forward", ("forward",)),
            ("new tab", ("new tab",)),
        )

        existing_names = {(node.name or "").lower() for node in interactive_nodes}
        for label, keywords in browser_buttons:
            if label in existing_names:
                continue
            button_control = self._find_descendant(
                window,
                lambda elem, keys=keywords: self._matches_named_button(elem, keys),
                max_depth=15,
            )
            if button_control:
                button_node = self._create_interactive_node(button_control, app_name)
                if button_node:
                    self._append_unique_interactive(interactive_nodes, button_node)
                    existing_names.add((button_node.name or "").lower())
