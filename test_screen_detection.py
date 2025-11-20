"""
Diagnostic script to test screen element detection in Windows-Use
This script tests the desktop tool that identifies items on the screen
"""

import sys
import os
from pprint import pprint

# Add the project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from windows_use.desktop.service import Desktop
from windows_use.tree.service import Tree

def print_separator(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_desktop_state():
    """Test basic desktop state retrieval"""
    print_separator("Testing Desktop State Retrieval")
    
    desktop = Desktop()
    
    print("Getting desktop state (without vision)...")
    state = desktop.get_state(use_vision=False)
    
    # Print active app info
    print("\n[ACTIVE APP]")
    if state.active_app:
        print(f"  Name: {state.active_app.name}")
        print(f"  Status: {state.active_app.status}")
        print(f"  Size: {state.active_app.size.width}x{state.active_app.size.height}")
        print(f"  Handle: {state.active_app.handle}")
        if state.active_app.process_name:
            print(f"  Process: {state.active_app.process_name}")
    else:
        print("  No active app detected!")
    
    # Print background apps
    print(f"\n[BACKGROUND APPS] ({len(state.apps)} apps)")
    for i, app in enumerate(state.apps[:5], 1):  # Show first 5
        print(f"  {i}. {app.name} ({app.status})")
    
    return desktop, state

def test_element_detection(desktop, state):
    """Test element detection on the active window"""
    print_separator("Testing Element Detection")
    
    if not state.tree_state:
        print("ERROR: No tree state available!")
        return
    
    # Print interactive elements
    print(f"[INTERACTIVE ELEMENTS] ({len(state.tree_state.interactive_nodes)} found)")
    if len(state.tree_state.interactive_nodes) == 0:
        print("  WARNING: No interactive elements detected!")
        print("  This could indicate a problem with element detection.")
    else:
        for i, node in enumerate(state.tree_state.interactive_nodes[:10], 1):  # Show first 10
            print(f"  {i}. {node.control_type}: '{node.name}' @ ({node.center.x}, {node.center.y})")
            print(f"      App: {node.app_name}")
            print(f"      BBox: ({node.bounding_box.left}, {node.bounding_box.top}) - "
                  f"({node.bounding_box.right}, {node.bounding_box.bottom})")
    
    # Print informative elements (text)
    print(f"\n[INFORMATIVE ELEMENTS] ({len(state.tree_state.informative_nodes)} found)")
    if len(state.tree_state.informative_nodes) == 0:
        print("  WARNING: No informative elements detected!")
    else:
        for i, node in enumerate(state.tree_state.informative_nodes[:10], 1):  # Show first 10
            text = node.name[:50] + "..." if len(node.name) > 50 else node.name
            print(f"  {i}. '{text}' (App: {node.app_name})")
    
    # Print scrollable elements
    print(f"\n[SCROLLABLE ELEMENTS] ({len(state.tree_state.scrollable_nodes)} found)")
    if len(state.tree_state.scrollable_nodes) > 0:
        for i, node in enumerate(state.tree_state.scrollable_nodes[:5], 1):  # Show first 5
            print(f"  {i}. {node.control_type}: '{node.name}' @ ({node.center.x}, {node.center.y})")
            print(f"      H-Scroll: {node.horizontal_scrollable}, V-Scroll: {node.vertical_scrollable}")

def test_precise_detection(desktop):
    """Test precise element detection for the active app"""
    print_separator("Testing Precise Detection on Active App")
    
    apps = desktop.get_apps()
    active_app = desktop._get_foreground_app(apps)
    
    if not active_app:
        print("ERROR: Could not get foreground app!")
        return
    
    print(f"Testing precise detection on: {active_app.name}")
    
    # Get state with target app
    state = desktop.get_state(use_vision=False, target_app=active_app.name)
    
    print(f"\n[PRECISE DETECTION RESULTS]")
    print(f"  Interactive: {len(state.tree_state.interactive_nodes)} elements")
    print(f"  Informative: {len(state.tree_state.informative_nodes)} elements")
    print(f"  Scrollable: {len(state.tree_state.scrollable_nodes)} elements")
    
    if len(state.tree_state.interactive_nodes) == 0:
        print("\n  WARNING: Precise detection found no interactive elements!")
        print("  This is the main problem - elements are not being detected.")
    
    return state

def test_uiautomation_access():
    """Test direct uiautomation library access"""
    print_separator("Testing Direct UI Automation Access")
    
    try:
        from uiautomation import GetRootControl, GetForegroundWindow, ControlFromHandle
        
        # Get foreground window
        print("Getting foreground window...")
        fg_hwnd = GetForegroundWindow()
        print(f"  Foreground window handle: {fg_hwnd}")
        
        # Get control from handle
        print("\nGetting control from handle...")
        control = ControlFromHandle(fg_hwnd)
        print(f"  Control Name: {control.Name}")
        print(f"  Control Type: {control.ControlTypeName}")
        print(f"  Control Visible: {control.IsControlElement}")
        print(f"  Bounding Box: {control.BoundingRectangle}")
        
        # Get children
        print("\nGetting children...")
        children = control.GetChildren()
        print(f"  Children count: {len(children)}")
        
        if len(children) > 0:
            print("\n  First 5 children:")
            for i, child in enumerate(children[:5], 1):
                try:
                    print(f"    {i}. {child.ControlTypeName}: '{child.Name}' "
                          f"(Enabled: {child.IsEnabled}, Visible: {not child.IsOffscreen})")
                except Exception as e:
                    print(f"    {i}. Error reading child: {e}")
        else:
            print("\n  WARNING: No children found! This could indicate UI Automation access issues.")
        
        # Try to walk deeper
        print("\nWalking tree deeper (2 levels)...")
        element_count = 0
        for child in children[:3]:  # Only check first 3 children
            try:
                grandchildren = child.GetChildren()
                element_count += len(grandchildren)
                print(f"  {child.ControlTypeName} has {len(grandchildren)} children")
            except Exception as e:
                print(f"  Error getting grandchildren: {e}")
        
        print(f"\nTotal elements found in depth-2 search: {element_count}")
        
        if element_count == 0:
            print("  WARNING: No deep elements found! UI tree may not be accessible.")
        
    except Exception as e:
        print(f"ERROR testing UI Automation: {e}")
        import traceback
        traceback.print_exc()

def run_diagnostics():
    """Run all diagnostic tests"""
    print("\n")
    print("="*80)
    print("  WINDOWS-USE SCREEN DETECTION DIAGNOSTICS")
    print("="*80)
    
    try:
        # Test 1: Basic desktop state
        desktop, state = test_desktop_state()
        
        # Test 2: Element detection
        test_element_detection(desktop, state)
        
        # Test 3: Precise detection
        test_precise_detection(desktop)
        
        # Test 4: Direct UI Automation
        test_uiautomation_access()
        
        # Summary
        print_separator("DIAGNOSTIC SUMMARY")
        
        total_elements = (len(state.tree_state.interactive_nodes) + 
                         len(state.tree_state.informative_nodes) + 
                         len(state.tree_state.scrollable_nodes))
        
        print(f"Total elements detected: {total_elements}")
        
        if total_elements == 0:
            print("\n❌ PROBLEM DETECTED: No elements are being detected on screen!")
            print("\nPossible causes:")
            print("  1. UI Automation may not have permissions")
            print("  2. The active window may not expose UI elements")
            print("  3. Element detection filters may be too restrictive")
            print("  4. The window may not be in a stable state")
            print("\nRecommended actions:")
            print("  1. Try running as Administrator")
            print("  2. Test with a simple app like Calculator or Notepad")
            print("  3. Check if the app uses standard Windows controls")
            print("  4. Review the element detection logic in tree/service.py")
        elif total_elements < 5:
            print("\n⚠️  WARNING: Very few elements detected")
            print("  This may indicate partial detection issues")
        else:
            print("\n✅ Element detection appears to be working")
            print(f"  Found {len(state.tree_state.interactive_nodes)} interactive elements")
            print(f"  Found {len(state.tree_state.informative_nodes)} informative elements")
        
    except Exception as e:
        print(f"\n❌ ERROR during diagnostics: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_diagnostics()

