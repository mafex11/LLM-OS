from windows_use.tree.views import TreeElementNode, TextElementNode, ScrollElementNode, Center, BoundingBox, TreeState
from windows_use.tree.config import INTERACTIVE_CONTROL_TYPE_NAMES,INFORMATIVE_CONTROL_TYPE_NAMES, DEFAULT_ACTIONS
from windows_use.tree.precise_detection import PreciseElementDetector
from uiautomation import GetRootControl,Control,ImageControl,ScrollPattern
from windows_use.tree.utils import random_point_within_bounding_box
from windows_use.desktop.config import AVOIDED_APPS, EXCLUDED_APPS
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from PIL import Image, ImageFont, ImageDraw
from typing import TYPE_CHECKING
from time import sleep
import random
import signal

if TYPE_CHECKING:
    from windows_use.desktop.service import Desktop

class Tree:
    def __init__(self,desktop:'Desktop'):
        self.desktop=desktop
        self.precise_detector = PreciseElementDetector(desktop)
        screen_size = self.desktop.get_screen_size()
        from windows_use.desktop.views import Size
        self.screen_box = BoundingBox(
            top=0, left=0, bottom=screen_size.height if isinstance(screen_size, Size) else screen_size[1],
            right=screen_size.width if isinstance(screen_size, Size) else screen_size[0],
            width=screen_size.width if isinstance(screen_size, Size) else screen_size[0],
            height=screen_size.height if isinstance(screen_size, Size) else screen_size[1]
        )
        self.dom_bounding_box = None

    def get_state(self)->TreeState:
        sleep(0.05)  # Optimized: reduced from 0.2s to 50ms
        # Get the root control of the desktop
        root=GetRootControl()
        interactive_nodes,informative_nodes,scrollable_nodes=self.get_appwise_nodes(node=root)
        return TreeState(interactive_nodes=interactive_nodes,informative_nodes=informative_nodes,scrollable_nodes=scrollable_nodes)
    
    def get_precise_state(self, window: Control | None = None) -> TreeState:
        """
        Get element detection focused on a specific window. Falls back to regular
        detection when a window isn't provided.
        """
        sleep(0.05)  # Optimized: reduced from 0.2s to 50ms
        if window is None:
            root = GetRootControl()
            interactive_nodes, informative_nodes, scrollable_nodes = self.get_appwise_nodes(node=root)
            return TreeState(
                interactive_nodes=interactive_nodes,
                informative_nodes=informative_nodes,
                scrollable_nodes=scrollable_nodes,
            )

        window_name = window.Name.strip() or window.ClassName or "Window"
        interactive_nodes, informative_nodes, scrollable_nodes = self.precise_detector.get_elements_for_window(
            window, window_name
        )

        # Some applications expose controls lazily; fall back to the generic traversal
        # when precise detection yields no metadata.
        if not interactive_nodes and not informative_nodes and not scrollable_nodes:
            interactive_nodes, informative_nodes, scrollable_nodes = self.get_nodes(
                window, self.desktop.is_app_browser(window)
            )

        return TreeState(
            interactive_nodes=interactive_nodes,
            informative_nodes=informative_nodes,
            scrollable_nodes=scrollable_nodes,
        )
    
    def iou_bounding_box(self, window_box, element_box) -> BoundingBox:
        """Calculate intersection of element with window and screen boundaries"""
        # Step 1: Intersection of element and window
        intersection_left = max(window_box.left, element_box.left)
        intersection_top = max(window_box.top, element_box.top)
        intersection_right = min(window_box.right, element_box.right)
        intersection_bottom = min(window_box.bottom, element_box.bottom)

        # Step 2: Clamp to screen boundaries
        intersection_left = max(self.screen_box.left, intersection_left)
        intersection_top = max(self.screen_box.top, intersection_top)
        intersection_right = min(self.screen_box.right, intersection_right)
        intersection_bottom = min(self.screen_box.bottom, intersection_bottom)

        # Step 3: Validate intersection
        if (intersection_right > intersection_left and intersection_bottom > intersection_top):
            bounding_box = BoundingBox(
                left=intersection_left,
                top=intersection_top,
                right=intersection_right,
                bottom=intersection_bottom,
                width=intersection_right - intersection_left,
                height=intersection_bottom - intersection_top
            )
        else:
            # No valid visible intersection
            bounding_box = BoundingBox(
                left=0, top=0, right=0, bottom=0, width=0, height=0
            )
        return bounding_box
    
    def get_appwise_nodes(self,node:Control) -> tuple[list[TreeElementNode],list[TextElementNode]]:
        apps:list[Control]=[]

        for app in node.GetChildren():
            if app.ClassName in EXCLUDED_APPS:
                continue
            if app.ClassName in AVOIDED_APPS:
                continue
            if self.desktop.is_app_visible(app):
                apps.append(app)

        interactive_nodes,informative_nodes,scrollable_nodes=[],[],[]
        # OPTIMIZATION: Parallel traversal with shorter timeouts to prevent hanging
        # CRITICAL: Browsers can hang for 20-40 seconds, so we use aggressive timeouts
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_node = {executor.submit(self.get_nodes, app,self.desktop.is_app_browser(app)): app for app in apps}
            for future in as_completed(future_to_node, timeout=8.0):  # Reduced from 10s to 8s
                try:
                    # CRITICAL: 2 second timeout per app to prevent browser hangs
                    result = future.result(timeout=2.0)  # Reduced from 3s to 2s per app
                    if result:
                        element_nodes,text_nodes,scroll_nodes=result
                        interactive_nodes.extend(element_nodes)
                        informative_nodes.extend(text_nodes)
                        scrollable_nodes.extend(scroll_nodes)
                except FutureTimeoutError:
                    app_name = "Unknown"
                    try:
                        app_name = future_to_node[future].Name
                    except:
                        pass
                    print(f"Timeout processing node {app_name} - skipping (likely browser with too many elements)")
                except Exception as e:
                    app_name = "Unknown"
                    try:
                        app_name = future_to_node[future].Name
                    except:
                        pass
                    print(f"Error processing node {app_name}: {e}")
        return interactive_nodes,informative_nodes,scrollable_nodes

    def get_nodes(self, node: Control, is_browser=False) -> tuple[list[TreeElementNode],list[TextElementNode],list[ScrollElementNode]]:
        interactive_nodes, dom_interactive_nodes, informative_nodes, scrollable_nodes = [], [], [], []
        app_name=node.Name.strip()
        app_name='Desktop' if node.ClassName=='Progman' else app_name
        window_bounding_box = node.BoundingRectangle
        
        # OPTIMIZATION: Limit max elements to prevent hanging on complex pages
        max_interactive_elements = 150  # Stop after finding 150 interactive elements
        max_total_elements = 300  # Stop after processing 300 total elements
        elements_processed = 0
        
        def is_element_visible(node:Control,threshold:int=0):
            is_control=node.IsControlElement
            box=node.BoundingRectangle
            if box.isempty():
                return False
            width=box.width()
            height=box.height()
            area=width*height
            is_offscreen=(not node.IsOffscreen) or node.ControlTypeName in ['EditControl']
            return area > threshold and is_offscreen and is_control
    
        def is_element_enabled(node:Control):
            try:
                return node.IsEnabled
            except Exception:
                return False
            
        def is_default_action(node:Control):
            legacy_pattern=node.GetLegacyIAccessiblePattern()
            default_action=legacy_pattern.DefaultAction.title()
            if default_action in DEFAULT_ACTIONS:
                return True
            return False
        
        def is_element_image(node:Control):
            if isinstance(node,ImageControl):
                if node.LocalizedControlType=='graphic' or not node.IsKeyboardFocusable:
                    return True
            return False
        
        def is_element_text(node:Control):
            try:
                if node.ControlTypeName in INFORMATIVE_CONTROL_TYPE_NAMES:
                    if is_element_visible(node) and is_element_enabled(node) and not is_element_image(node):
                        return True
            except Exception:
                return False
            return False
        
        def is_element_scrollable(node:Control):
            try:
                scroll_pattern:ScrollPattern=node.GetScrollPattern()
                return scroll_pattern.VerticallyScrollable or scroll_pattern.HorizontallyScrollable
            except Exception:
                return False
            
        def is_keyboard_focusable(node:Control):
            try:
                if node.ControlTypeName in set(['EditControl','ButtonControl','CheckBoxControl','RadioButtonControl','TabItemControl']):
                    return True
                return node.IsKeyboardFocusable
            except Exception:
                return False
            
        def element_has_child_element(node:Control,control_type:str,child_control_type:str):
            if node.LocalizedControlType==control_type:
                first_child=node.GetFirstChildControl()
                if first_child is None:
                    return False
                return first_child.LocalizedControlType==child_control_type
            
        def group_has_no_name(node:Control):
            try:
                if node.ControlTypeName=='GroupControl':
                    if not node.Name.strip():
                        return True
                return False
            except Exception:
                return False
            
        def is_element_interactive(node:Control):
            try:
                if node.ControlTypeName in INTERACTIVE_CONTROL_TYPE_NAMES:
                    if is_element_visible(node) and is_element_enabled(node) and (not is_element_image(node) or is_keyboard_focusable(node)):
                        return True
                elif node.ControlTypeName=='GroupControl' and is_browser:
                    if is_element_visible(node) and is_element_enabled(node) and (is_default_action(node) or is_keyboard_focusable(node)):
                        return True
                # elif node.ControlTypeName=='GroupControl' and not is_browser:
                #     if is_element_visible and is_element_enabled(node) and is_default_action(node):
                #         return True
            except Exception:
                return False
            return False
        
        def dom_correction(node:Control):
            if element_has_child_element(node,'list item','link') or element_has_child_element(node,'item','link'):
                dom_interactive_nodes.pop()
                return None
            elif node.ControlTypeName=='GroupControl':
                dom_interactive_nodes.pop()
                if is_keyboard_focusable(node):
                    child=node
                    try:
                        while child.GetFirstChildControl() is not None:
                            if child.ControlTypeName in INTERACTIVE_CONTROL_TYPE_NAMES:
                                return None
                            child=child.GetFirstChildControl()
                    except Exception:
                        return None
                    if child.ControlTypeName!='TextControl':
                        return None
                    legacy_pattern=node.GetLegacyIAccessiblePattern()
                    value=legacy_pattern.Value if legacy_pattern else ""
                    element_bounding_box = node.BoundingRectangle
                    bounding_box=self.iou_bounding_box(self.dom_bounding_box, element_bounding_box)
                    center = bounding_box.get_center() if hasattr(bounding_box, 'get_center') else Center(x=(bounding_box.left + bounding_box.right)//2, y=(bounding_box.top + bounding_box.bottom)//2)
                    is_focused=node.HasKeyboardFocus
                    dom_interactive_nodes.append(TreeElementNode(
                        name=child.Name.strip() or "''",
                        control_type=node.LocalizedControlType,
                        shortcut=node.AcceleratorKey or "''",
                        bounding_box=bounding_box,
                        center=center,
                        app_name=app_name
                    ))
            elif element_has_child_element(node,'link','heading'):
                dom_interactive_nodes.pop()
                node=node.GetFirstChildControl()
                control_type='link'
                legacy_pattern=node.GetLegacyIAccessiblePattern()
                value=legacy_pattern.Value if legacy_pattern else node.Name.strip()
                element_bounding_box = node.BoundingRectangle
                bounding_box=self.iou_bounding_box(self.dom_bounding_box, element_bounding_box)
                center = bounding_box.get_center() if hasattr(bounding_box, 'get_center') else Center(x=(bounding_box.left + bounding_box.right)//2, y=(bounding_box.top + bounding_box.bottom)//2)
                is_focused=node.HasKeyboardFocus
                dom_interactive_nodes.append(TreeElementNode(
                    name=node.Name.strip() or "''",
                    control_type=control_type,
                    shortcut=node.AcceleratorKey or "''",
                    bounding_box=bounding_box,
                    center=center,
                    app_name=app_name
                ))
            
        def tree_traversal(node: Control, is_dom: bool = False, is_dialog: bool = False, depth: int = 0, max_depth: int = 30):
            nonlocal elements_processed
            
            # OPTIMIZATION: Stop early if we've processed enough elements
            if elements_processed >= max_total_elements:
                return None
            if len(interactive_nodes) + len(dom_interactive_nodes) >= max_interactive_elements:
                return None
            
            # Prevent infinite recursion by limiting depth
            if depth > max_depth:
                return None
            
            elements_processed += 1
            
            # Checks to skip the nodes that are not interactive
            if node.IsOffscreen and (node.ControlTypeName not in set(["GroupControl","EditControl","TitleBarControl"])) and node.ClassName not in set(["Popup","Windows.UI.Core.CoreComponentInputSource"]):
                return None
            
            # Check if element is scrollable
            if is_element_scrollable(node):
                scroll_pattern:ScrollPattern=node.GetScrollPattern()
                box = node.BoundingRectangle
                x,y=random_point_within_bounding_box(node=node,scale_factor=0.8)
                center = Center(x=x,y=y)
                scrollable_nodes.append(ScrollElementNode(
                    name=node.Name.strip() or node.AutomationId or node.LocalizedControlType.capitalize() or "''",
                    app_name=app_name,
                    control_type=node.LocalizedControlType.title(),
                    bounding_box=BoundingBox(left=box.left,top=box.top,right=box.right,bottom=box.bottom,width=box.width(),height=box.height()),
                    center=center,
                    horizontal_scrollable=scroll_pattern.HorizontallyScrollable,
                    vertical_scrollable=scroll_pattern.VerticallyScrollable
                ))
            
            # Check if element is interactive
            if is_element_interactive(node):
                legacy_pattern=node.GetLegacyIAccessiblePattern()
                value=legacy_pattern.Value.strip() if (legacy_pattern and legacy_pattern.Value) else ""
                is_focused=node.HasKeyboardFocus
                name=node.Name.strip()
                element_bounding_box = node.BoundingRectangle
                
                if is_browser and is_dom:
                    # DOM element - use DOM bounding box
                    bounding_box=self.iou_bounding_box(self.dom_bounding_box, element_bounding_box)
                    center = bounding_box.get_center() if hasattr(bounding_box, 'get_center') else Center(x=(bounding_box.left + bounding_box.right)//2, y=(bounding_box.top + bounding_box.bottom)//2)
                    tree_node=TreeElementNode(
                        name=name or "''",
                        control_type=node.LocalizedControlType.title(),
                        shortcut=node.AcceleratorKey or "''",
                        bounding_box=bounding_box,
                        center=center,
                        app_name=app_name
                    )
                    dom_interactive_nodes.append(tree_node)
                    dom_correction(node)
                else:
                    # Regular element - use window bounding box
                    bounding_box=self.iou_bounding_box(window_bounding_box, element_bounding_box)
                    center = bounding_box.get_center() if hasattr(bounding_box, 'get_center') else Center(x=(bounding_box.left + bounding_box.right)//2, y=(bounding_box.top + bounding_box.bottom)//2)
                    tree_node=TreeElementNode(
                        name=name or "''",
                        control_type=node.LocalizedControlType.title(),
                        shortcut=node.AcceleratorKey or "''",
                        bounding_box=bounding_box,
                        center=center,
                        app_name=app_name
                    )
                    interactive_nodes.append(tree_node)
            elif is_element_text(node):
                informative_nodes.append(TextElementNode(
                    name=node.Name.strip() or "''",
                    app_name=app_name
                ))
            
            # Get children for recursion
            children=node.GetChildren()
            
            # Recursively traverse (right to left for normal apps, left to right for DOM)
            for child in (children if is_dom else children[::-1]):
                # Check if the child is a browser DOM element - handle all browser types
                browser_dom_classes = [
                    "Chrome_RenderWidgetHostHWND",  # Chrome, Edge, Opera (Chromium-based)
                    "Internet Explorer_Server",      # Internet Explorer, old Edge
                    "MozillaWindowClass"             # Firefox
                ]
                if is_browser and child.ClassName in browser_dom_classes:
                    bounding_box=child.BoundingRectangle
                    # Only set DOM bounding box if it's valid
                    if not bounding_box.isempty() and bounding_box.width() > 0 and bounding_box.height() > 0:
                        self.dom_bounding_box=BoundingBox(
                            left=bounding_box.left, top=bounding_box.top,
                            right=bounding_box.right, bottom=bounding_box.bottom,
                            width=bounding_box.width(), height=bounding_box.height()
                        )
                        # Enter DOM subtree with DOM mode enabled
                        tree_traversal(child, is_dom=True, is_dialog=is_dialog, depth=depth+1, max_depth=max_depth)
                # Check if the child is a dialog/window
                elif child.ControlType == 0xC370:  # WindowControl = 0xC370
                    from uiautomation import WindowControl
                    if isinstance(child, WindowControl) and not child.IsOffscreen:
                        if is_dom:
                            bounding_box=child.BoundingRectangle
                            if bounding_box.width() > 0.8 * self.dom_bounding_box.width:
                                # Window covers majority of DOM - clear DOM nodes
                                dom_interactive_nodes.clear()
                        else:
                            # Check if window is modal
                            try:
                                window_pattern=child.GetWindowPattern()
                                if window_pattern and window_pattern.IsModal:
                                    # Modal window - clear interactive nodes
                                    interactive_nodes.clear()
                            except Exception:
                                pass
                    # Enter dialog subtree
                    tree_traversal(child, is_dom=is_dom, is_dialog=True, depth=depth+1, max_depth=max_depth)
                else:
                    # Normal non-dialog children
                    tree_traversal(child, is_dom=is_dom, is_dialog=is_dialog, depth=depth+1, max_depth=max_depth)

        tree_traversal(node, is_dom=False, is_dialog=False)
        
        # Merge DOM interactive nodes with regular interactive nodes
        interactive_nodes.extend(dom_interactive_nodes)
        
        return (interactive_nodes,informative_nodes,scrollable_nodes)
    
    def get_random_color(self):
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def annotated_screenshot(self, nodes: list[TreeElementNode],scale:float=0.7) -> Image.Image:
        screenshot = self.desktop.get_screenshot(scale=scale)
        sleep(0.25)
        # Add padding
        padding = 20
        width = screenshot.width + (2 * padding)
        height = screenshot.height + (2 * padding)
        padded_screenshot = Image.new("RGB", (width, height), color=(255, 255, 255))
        padded_screenshot.paste(screenshot, (padding, padding))

        draw = ImageDraw.Draw(padded_screenshot)
        font_size = 12
        try:
            font = ImageFont.truetype('arial.ttf', font_size)
        except IOError:
            font = ImageFont.load_default()

        def get_random_color():
            return "#{:06x}".format(random.randint(0, 0xFFFFFF))

        def draw_annotation(label, node: TreeElementNode):
            box = node.bounding_box
            color = get_random_color()

            # Scale and pad the bounding box also clip the bounding box
            adjusted_box = (
                int(box.left * scale) + padding,
                int(box.top * scale) + padding,
                int(box.right * scale) + padding,
                int(box.bottom * scale) + padding
            )
            # Draw bounding box
            draw.rectangle(adjusted_box, outline=color, width=2)

            # Label dimensions
            label_width = draw.textlength(str(label), font=font)
            label_height = font_size
            left, top, right, bottom = adjusted_box

            # Label position above bounding box
            label_x1 = right - label_width
            label_y1 = top - label_height - 4
            label_x2 = label_x1 + label_width
            label_y2 = label_y1 + label_height + 4

            # Draw label background and text
            draw.rectangle([(label_x1, label_y1), (label_x2, label_y2)], fill=color)
            draw.text((label_x1 + 2, label_y1 + 2), str(label), fill=(255, 255, 255), font=font)

        # Draw annotations in parallel
        with ThreadPoolExecutor() as executor:
            executor.map(draw_annotation, range(len(nodes)), nodes)
        return padded_screenshot
    
    def get_annotated_image_data(self)->tuple[Image.Image,list[TreeElementNode]]:
        node=GetRootControl()
        nodes,_,_=self.get_appwise_nodes(node=node)
        screenshot=self.annotated_screenshot(nodes=nodes,scale=1.0)
        return screenshot,nodes