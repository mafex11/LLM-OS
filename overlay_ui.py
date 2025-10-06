import tkinter as tk
from tkinter import ttk
import threading
import time
from datetime import datetime
import queue
from typing import Dict, Any, Optional

class AgentOverlayUI:
    """
    Transparent overlay UI that shows agent execution status in real-time.
    Stays always on top without interfering with window switching.
    """
    
    def __init__(self):
        self.root = None
        self.status_queue = queue.Queue()
        self.is_running = False
        self.current_status = {
            'iteration': 0,
            'max_steps': 30,
            'phase': 'Ready',
            'action': '',
            'details': '',
            'evaluate': '',
            'memory': '',
            'plan': '',
            'thought': '',
            'tool_result': '',
            'timestamp': ''
        }
        self.ui_thread = None
        
    def start(self):
        """Start the overlay UI in a separate thread"""
        if self.is_running:
            return
            
        self.is_running = True
        self.ui_thread = threading.Thread(target=self._create_ui, daemon=True)
        self.ui_thread.start()
        
    def stop(self):
        """Stop the overlay UI"""
        self.is_running = False
        if self.root:
            self.root.quit()
            self.root.destroy()
            
    def update_status(self, **kwargs):
        """Update status information (thread-safe)"""
        try:
            # Add timestamp
            kwargs['timestamp'] = datetime.now().strftime("%H:%M:%S")
            
            # Put update in queue for UI thread
            self.status_queue.put(kwargs)
        except Exception as e:
            print(f"Error updating overlay status: {e}")
            
    def _create_ui(self):
        """Create the overlay UI window"""
        try:
            self.root = tk.Tk()
            self.root.title("Agent Status Overlay")
            
            # Make window transparent and always on top
            self.root.attributes('-topmost', True)
            self.root.attributes('-alpha', 0.85)  # 85% opacity
            
            # Remove window decorations
            self.root.overrideredirect(True)
            
            # Set window size and position
            self.root.geometry("400x300+50+50")
            
            # Configure style
            self.root.configure(bg='#1a1a1a')
            
            # Create main frame
            main_frame = tk.Frame(self.root, bg='#1a1a1a', padx=10, pady=10)
            main_frame.pack(fill='both', expand=True)
            
            # Title
            title_label = tk.Label(
                main_frame, 
                text="🤖 Agent Status", 
                font=('Arial', 12, 'bold'),
                fg='#00ff88',
                bg='#1a1a1a'
            )
            title_label.pack(pady=(0, 10))
            
            # Status grid frame
            status_frame = tk.Frame(main_frame, bg='#1a1a1a')
            status_frame.pack(fill='both', expand=True)
            
            # Create status labels
            self.labels = {}
            status_items = [
                ('phase', 'Phase', '#ff6b6b'),
                ('iteration', 'Step', '#4ecdc4'),
                ('action', 'Action', '#45b7d1'),
                ('details', 'Details', '#96ceb4'),
                ('evaluate', 'Evaluate', '#ffeaa7'),
                ('memory', 'Memory', '#dda0dd'),
                ('plan', 'Plan', '#98d8c8'),
                ('thought', 'Thought', '#f7dc6f'),
                ('tool_result', 'Result', '#bb8fce'),
                ('timestamp', 'Time', '#85c1e9')
            ]
            
            for i, (key, label, color) in enumerate(status_items):
                row = i // 2
                col = (i % 2) * 2
                
                # Label
                tk.Label(
                    status_frame,
                    text=f"{label}:",
                    font=('Arial', 8, 'bold'),
                    fg=color,
                    bg='#1a1a1a'
                ).grid(row=row, column=col, sticky='w', padx=(0, 5), pady=2)
                
                # Value
                value_label = tk.Label(
                    status_frame,
                    text="",
                    font=('Arial', 8),
                    fg='white',
                    bg='#1a1a1a',
                    wraplength=180,
                    justify='left'
                )
                value_label.grid(row=row, column=col+1, sticky='w', pady=2)
                
                self.labels[key] = value_label
            
            # Progress bar
            self.progress = ttk.Progressbar(
                main_frame,
                mode='determinate',
                style='Custom.Horizontal.TProgressbar'
            )
            self.progress.pack(fill='x', pady=(10, 0))
            
            # Configure progress bar style
            style = ttk.Style()
            style.theme_use('clam')
            style.configure(
                'Custom.Horizontal.TProgressbar',
                background='#00ff88',
                troughcolor='#2d2d2d',
                borderwidth=0,
                lightcolor='#00ff88',
                darkcolor='#00ff88'
            )
            
            # Control buttons frame
            button_frame = tk.Frame(main_frame, bg='#1a1a1a')
            button_frame.pack(fill='x', pady=(10, 0))
            
            # Minimize button
            minimize_btn = tk.Button(
                button_frame,
                text="−",
                font=('Arial', 10, 'bold'),
                fg='white',
                bg='#444444',
                activebackground='#555555',
                borderwidth=0,
                width=3,
                command=self._minimize_window
            )
            minimize_btn.pack(side='left', padx=(0, 5))
            
            # Close button
            close_btn = tk.Button(
                button_frame,
                text="×",
                font=('Arial', 10, 'bold'),
                fg='white',
                bg='#ff4444',
                activebackground='#ff6666',
                borderwidth=0,
                width=3,
                command=self._close_window
            )
            close_btn.pack(side='right')
            
            # Drag functionality
            self._setup_drag()
            
            # Start update loop
            self._update_loop()
            
            # Start the UI
            self.root.mainloop()
            
        except Exception as e:
            print(f"Error creating overlay UI: {e}")
            
    def _setup_drag(self):
        """Setup window dragging functionality"""
        def start_drag(event):
            self.root.start_x = event.x
            self.root.start_y = event.y
            
        def drag_window(event):
            x = self.root.winfo_x() + event.x - self.root.start_x
            y = self.root.winfo_y() + event.y - self.root.start_y
            self.root.geometry(f"+{x}+{y}")
            
        # Bind drag events to title
        title_label = None
        for child in self.root.winfo_children():
            if isinstance(child, tk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, tk.Label) and grandchild['text'] == "🤖 Agent Status":
                        title_label = grandchild
                        break
                if title_label:
                    break
                    
        if title_label:
            title_label.bind("<Button-1>", start_drag)
            title_label.bind("<B1-Motion>", drag_window)
            
    def _minimize_window(self):
        """Minimize the window"""
        if self.root.state() == 'normal':
            self.root.state('withdrawn')
        else:
            self.root.state('normal')
            
    def _close_window(self):
        """Close the window"""
        self.stop()
        
    def _update_loop(self):
        """Main update loop for the UI"""
        if not self.is_running or not self.root:
            return
            
        try:
            # Process status updates from queue
            while not self.status_queue.empty():
                try:
                    updates = self.status_queue.get_nowait()
                    self.current_status.update(updates)
                except queue.Empty:
                    break
                    
            # Update UI with current status
            self._update_ui()
            
            # Schedule next update
            self.root.after(100, self._update_loop)
            
        except Exception as e:
            print(f"Error in update loop: {e}")
            
    def _update_ui(self):
        """Update the UI with current status"""
        try:
            if not self.root or not self.labels:
                return
                
            # Update labels
            for key, label in self.labels.items():
                value = self.current_status.get(key, '')
                if key == 'iteration':
                    max_steps = self.current_status.get('max_steps', 30)
                    value = f"{value}/{max_steps}"
                elif key == 'tool_result' and value:
                    # Truncate long results
                    value = value[:100] + '...' if len(value) > 100 else value
                elif key == 'timestamp':
                    value = value
                    
                label.config(text=str(value))
                
            # Update progress bar
            iteration = self.current_status.get('iteration', 0)
            max_steps = self.current_status.get('max_steps', 30)
            if max_steps > 0:
                progress = (iteration / max_steps) * 100
                self.progress['value'] = progress
                
        except Exception as e:
            print(f"Error updating UI: {e}")

# Global overlay instance
overlay_instance = None

def start_overlay():
    """Start the overlay UI"""
    global overlay_instance
    if overlay_instance is None:
        overlay_instance = AgentOverlayUI()
        overlay_instance.start()
    return overlay_instance

def stop_overlay():
    """Stop the overlay UI"""
    global overlay_instance
    if overlay_instance:
        overlay_instance.stop()
        overlay_instance = None

def update_overlay_status(**kwargs):
    """Update overlay status (thread-safe)"""
    global overlay_instance
    if overlay_instance:
        overlay_instance.update_status(**kwargs)

if __name__ == "__main__":
    # Test the overlay
    overlay = start_overlay()
    
    # Simulate some status updates
    time.sleep(1)
    update_overlay_status(phase="Starting", iteration=1, action="Click Tool", details="Clicking on button")
    time.sleep(2)
    update_overlay_status(iteration=2, evaluate="Success", memory="Found similar task", plan="Continue with next step")
    time.sleep(2)
    update_overlay_status(phase="Completed", iteration=3, tool_result="Task completed successfully")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_overlay()

