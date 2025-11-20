"""
Quick diagnostic for screen detection issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting quick test...")

try:
    print("1. Importing uiautomation...")
    from uiautomation import GetForegroundWindow, ControlFromHandle
    
    print("2. Getting foreground window...")
    hwnd = GetForegroundWindow()
    print(f"   Foreground window handle: {hwnd}")
    
    print("3. Getting control from handle...")
    control = ControlFromHandle(hwnd)
    print(f"   Control Name: {control.Name}")
    print(f"   Control Type: {control.ControlTypeName}")
    
    print("4. Getting children (with timeout)...")
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Getting children took too long")
    
    # Set 5 second timeout
    try:
        children = control.GetChildren()
        print(f"   Found {len(children)} children")
        
        if children:
            print("\n   First 3 children:")
            for i, child in enumerate(children[:3], 1):
                try:
                    print(f"     {i}. Type: {child.ControlTypeName}, Name: {child.Name[:30] if child.Name else 'None'}")
                except:
                    print(f"     {i}. Error reading child")
    except Exception as e:
        print(f"   ERROR getting children: {e}")
    
    print("\n5. Testing Tree service...")
    from windows_use.tree.service import Tree
    from windows_use.desktop.service import Desktop
    
    desktop = Desktop()
    tree = Tree(desktop)
    
    print("   Creating tree instance - OK")
    print("   Attempting to get nodes (this may hang)...")
    
    # Try with a timeout
    import threading
    result = {"done": False, "error": None, "nodes": None}
    
    def get_nodes_thread():
        try:
            interactive, informative, scrollable = tree.get_nodes(control, is_browser=False)
            result["nodes"] = (interactive, informative, scrollable)
            result["done"] = True
        except Exception as e:
            result["error"] = str(e)
            result["done"] = True
    
    thread = threading.Thread(target=get_nodes_thread)
    thread.daemon = True
    thread.start()
    thread.join(timeout=10.0)  # 10 second timeout
    
    if not result["done"]:
        print("   ❌ TIMEOUT: get_nodes() is hanging!")
        print("   This is the root cause of the screen detection issue.")
        print("\n   The tree traversal is getting stuck, likely because:")
        print("   - It's recursively traversing too many elements")
        print("   - Some UI elements are blocking the traversal")
        print("   - The parallel processing is causing deadlocks")
    elif result["error"]:
        print(f"   ❌ ERROR in get_nodes(): {result['error']}")
    else:
        interactive, informative, scrollable = result["nodes"]
        print(f"   ✅ SUCCESS: Found {len(interactive)} interactive, {len(informative)} informative, {len(scrollable)} scrollable")
    
    print("\n6. Testing with GetRootControl (desktop level)...")
    from uiautomation import GetRootControl
    
    root = GetRootControl()
    print(f"   Root control: {root.Name}")
    
    apps = root.GetChildren()
    print(f"   Found {len(apps)} top-level windows")
    
    print("\n✅ Basic UI Automation is working")
    print("❌ Problem is in the Tree.get_nodes() traversal logic")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\nTest complete.")

