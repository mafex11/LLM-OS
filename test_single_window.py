"""
Test screen detection on a single window
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing single window detection\n")

try:
    from uiautomation import GetForegroundWindow, ControlFromHandle
    from windows_use.tree.service import Tree
    from windows_use.desktop.service import Desktop
    import time
    
    print("1. Getting foreground window...")
    hwnd = GetForegroundWindow()
    control = ControlFromHandle(hwnd)
    print(f"   Window: {control.Name}")
    print(f"   Type: {control.ControlTypeName}")
    
    print("\n2. Creating Tree and Desktop instances...")
    desktop = Desktop()
    tree = Tree(desktop)
    
    print("\n3. Getting nodes for this window (with timeout)...")
    start_time = time.time()
    
    try:
        is_browser = False
        try:
            from psutil import Process
            process = Process(control.ProcessId)
            is_browser = process.name() in ['chrome.exe', 'firefox.exe', 'msedge.exe']
        except:
            pass
        
        print(f"   Is browser: {is_browser}")
        
        # Try to get nodes
        interactive, informative, scrollable = tree.get_nodes(control, is_browser)
        
        elapsed = time.time() - start_time
        print(f"\n✅ Success in {elapsed:.2f} seconds!")
        print(f"   Interactive: {len(interactive)}")
        print(f"   Informative: {len(informative)}")
        print(f"   Scrollable: {len(scrollable)}")
        
        if interactive:
            print(f"\n   First 5 interactive elements:")
            for i, node in enumerate(interactive[:5], 1):
                print(f"     {i}. [{node.control_type}] {node.name} @ ({node.center.x}, {node.center.y})")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Failed after {elapsed:.2f} seconds: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n4. Now testing full desktop.get_state()...")
    print("   This calls get_appwise_nodes() which scans all visible windows...")
    
    start_time = time.time()
    try:
        # Set a shorter sleep
        import threading
        result = {"state": None, "error": None}
        
        def get_state_thread():
            try:
                result["state"] = desktop.get_state(use_vision=False)
            except Exception as e:
                result["error"] = str(e)
        
        thread = threading.Thread(target=get_state_thread)
        thread.daemon = True
        thread.start()
        thread.join(timeout=20.0)  # 20 second timeout
        
        elapsed = time.time() - start_time
        
        if result["state"]:
            state = result["state"]
            print(f"\n✅ Success in {elapsed:.2f} seconds!")
            print(f"   Interactive: {len(state.tree_state.interactive_nodes)}")
            print(f"   Informative: {len(state.tree_state.informative_nodes)}")
            print(f"   Scrollable: {len(state.tree_state.scrollable_nodes)}")
        elif result["error"]:
            print(f"\n❌ Error after {elapsed:.2f} seconds: {result['error']}")
        else:
            print(f"\n❌ TIMEOUT after {elapsed:.2f} seconds!")
            print("   The get_appwise_nodes() is hanging.")
            print("\n   This is the root cause of your screen detection problem.")
            print("   The parallel scanning of multiple windows is causing the hang.")
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Failed after {elapsed:.2f} seconds: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\nTest complete.")

