#!/usr/bin/env python3
"""
Test script for the overlay UI functionality
"""

import time
from overlay_ui import start_overlay, update_overlay_status, stop_overlay

def test_overlay():
    """Test the overlay UI with simulated agent execution"""
    print("Starting overlay test...")
    
    # Start overlay
    overlay = start_overlay()
    time.sleep(2)  # Give it time to start
    
    print("Testing status updates...")
    
    # Simulate agent execution phases
    phases = [
        {"phase": "Starting", "iteration": 1, "max_steps": 30, "action": "Click Tool", "details": "Clicking on button"},
        {"iteration": 1, "evaluate": "Success", "memory": "Found similar task", "plan": "Continue with next step", "thought": "Button should be clickable"},
        {"phase": "Executing", "iteration": 2, "action": "Type Tool", "details": "Typing text"},
        {"iteration": 2, "evaluate": "Success", "memory": "Previous action successful", "plan": "Type the required text", "thought": "Text field is ready"},
        {"phase": "Completed", "iteration": 3, "action": "Done Tool", "details": "Task completed", "tool_result": "Task completed successfully"}
    ]
    
    for phase in phases:
        print(f"Updating: {phase}")
        update_overlay_status(**phase)
        time.sleep(3)  # Wait to see the updates
    
    print("Test completed. Overlay should still be running.")
    print("Press Ctrl+C to stop the overlay.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping overlay...")
        stop_overlay()
        print("Overlay stopped.")

if __name__ == "__main__":
    test_overlay()
