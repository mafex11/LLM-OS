"""
Test the agent's ability to see and interact with screen elements
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Agent Vision Capabilities\n")
print("="*80)

try:
    from windows_use.desktop.service import Desktop
    from windows_use.tree.service import Tree
    
    # Test 1: Desktop State
    print("\n[TEST 1: Getting Desktop State]")
    desktop = Desktop()
    state = desktop.get_state(use_vision=False)
    
    print(f"✅ Active App: {state.active_app.name if state.active_app else 'None'}")
    print(f"✅ Background Apps: {len(state.apps)}")
    print(f"✅ Interactive Elements: {len(state.tree_state.interactive_nodes)}")
    print(f"✅ Informative Elements: {len(state.tree_state.informative_nodes)}")
    print(f"✅ Scrollable Elements: {len(state.tree_state.scrollable_nodes)}")
    
    # Test 2: Show sample elements
    print("\n[TEST 2: Sample Interactive Elements]")
    if state.tree_state.interactive_nodes:
        print(f"\nShowing first 10 interactive elements:")
        for i, node in enumerate(state.tree_state.interactive_nodes[:10], 1):
            print(f"  {i}. [{node.control_type}] '{node.name}' at ({node.center.x}, {node.center.y})")
        
        total = len(state.tree_state.interactive_nodes)
        if total > 10:
            print(f"  ... and {total - 10} more elements")
    else:
        print("❌ NO interactive elements found!")
    
    # Test 3: Show sample text elements
    print("\n[TEST 3: Sample Informative Elements (Text)]")
    if state.tree_state.informative_nodes:
        print(f"\nShowing first 10 text elements:")
        for i, node in enumerate(state.tree_state.informative_nodes[:10], 1):
            text = node.name[:60] + "..." if len(node.name) > 60 else node.name
            print(f"  {i}. '{text}'")
        
        total = len(state.tree_state.informative_nodes)
        if total > 10:
            print(f"  ... and {total - 10} more text elements")
    else:
        print("❌ NO informative elements found!")
    
    # Test 4: Test with specific app (if Calculator is open)
    print("\n[TEST 4: Precise Detection for Specific App]")
    apps = desktop.get_apps()
    calculator = None
    for app in apps:
        if "calculator" in app.name.lower():
            calculator = app
            break
    
    if calculator:
        print(f"✅ Found Calculator app: {calculator.name}")
        state_calc = desktop.get_state(use_vision=False, target_app="calculator")
        print(f"   Interactive Elements: {len(state_calc.tree_state.interactive_nodes)}")
        print(f"   Informative Elements: {len(state_calc.tree_state.informative_nodes)}")
        
        if state_calc.tree_state.interactive_nodes:
            print("\n   Calculator buttons detected:")
            for i, node in enumerate(state_calc.tree_state.interactive_nodes[:15], 1):
                print(f"     {i}. {node.name} at ({node.center.x}, {node.center.y})")
        else:
            print("   ❌ No Calculator buttons detected!")
    else:
        print("ℹ️  Calculator not open. Open Calculator to test specific app detection.")
    
    # Test 5: Check if elements are visible
    print("\n[TEST 5: Element Visibility Check]")
    if state.tree_state.interactive_nodes:
        sample_node = state.tree_state.interactive_nodes[0]
        print(f"Sample element: '{sample_node.name}'")
        print(f"  Type: {sample_node.control_type}")
        print(f"  Position: ({sample_node.center.x}, {sample_node.center.y})")
        print(f"  Bounding Box: {sample_node.bounding_box.width}x{sample_node.bounding_box.height}")
        print(f"  App: {sample_node.app_name}")
        
        # Check if position is on screen
        import pyautogui
        screen_width, screen_height = pyautogui.size()
        on_screen = (0 <= sample_node.center.x < screen_width and 
                    0 <= sample_node.center.y < screen_height)
        
        if on_screen:
            print(f"  ✅ Position is on screen ({screen_width}x{screen_height})")
        else:
            print(f"  ❌ Position is OFF screen! Screen size: {screen_width}x{screen_height}")
    
    # Summary
    print("\n" + "="*80)
    print("[SUMMARY]")
    total_elements = (len(state.tree_state.interactive_nodes) + 
                     len(state.tree_state.informative_nodes) + 
                     len(state.tree_state.scrollable_nodes))
    
    if total_elements > 50:
        print(f"✅ SCREEN DETECTION IS WORKING!")
        print(f"   Found {total_elements} total elements on screen")
        print(f"   - {len(state.tree_state.interactive_nodes)} interactive (buttons, inputs, etc.)")
        print(f"   - {len(state.tree_state.informative_nodes)} informative (text)")
        print(f"   - {len(state.tree_state.scrollable_nodes)} scrollable")
        print("\nThe agent should be able to see and interact with these elements.")
    elif total_elements > 0:
        print(f"⚠️  PARTIAL DETECTION")
        print(f"   Found {total_elements} elements (expected more)")
        print("   Some elements may not be visible to the agent.")
    else:
        print("❌ NO ELEMENTS DETECTED!")
        print("   The agent cannot see anything on screen.")
        print("\nPossible issues:")
        print("   1. No app is in focus")
        print("   2. The app doesn't use standard Windows controls")
        print("   3. Permission issues with UI Automation")
    
    print("\n" + "="*80)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

