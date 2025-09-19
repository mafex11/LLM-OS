"""
Desktop Loader Component

A visual loader overlay that can be displayed on the screen during agent task execution.
Uses tkinter for a lightweight, cross-platform solution.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Optional
import pyautogui
import atexit


class DesktopLoader:
    """
    A desktop overlay loader that shows progress and status during agent execution.
    """
    
    def __init__(self):
        self.root: Optional[tk.Tk] = None
        self.progress_var: Optional[tk.StringVar] = None
        self.status_var: Optional[tk.StringVar] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.is_running = False
        self.animation_thread: Optional[threading.Thread] = None
        self.stop_animation = False
        
    def _create_loader_window(self):
        """Create the loader window with progress bar and status text."""
        self.root = tk.Tk()
        self.root.title("Windows-Use Agent")
        self.root.configure(bg='#2b2b2b')
        
        # Make window always on top and remove window decorations
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window size and position (center of screen)
        window_width = 400
        window_height = 120
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create main frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="Windows-Use Agent", 
            font=('Arial', 14, 'bold'),
            fg='#00ff88',
            bg='#2b2b2b'
        )
        title_label.pack(pady=(0, 10))
        
        # Status text
        self.status_var = tk.StringVar(value="Initializing...")
        status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=('Arial', 10),
            fg='#ffffff',
            bg='#2b2b2b',
            wraplength=350
        )
        status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.StringVar(value="0%")
        progress_frame = tk.Frame(main_frame, bg='#2b2b2b')
        progress_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=300,
            style='Custom.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Progress percentage
        progress_label = tk.Label(
            progress_frame,
            textvariable=self.progress_var,
            font=('Arial', 9),
            fg='#cccccc',
            bg='#2b2b2b'
        )
        progress_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Configure progress bar style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Custom.Horizontal.TProgressbar',
            background='#00ff88',
            troughcolor='#404040',
            borderwidth=0,
            lightcolor='#00ff88',
            darkcolor='#00ff88'
        )
        
        # Add some padding
        self.root.update_idletasks()
        
    def _animate_progress(self):
        """Animate the progress bar with a pulsing effect."""
        while not self.stop_animation and self.is_running:
            if self.progress_bar:
                self.progress_bar['value'] = 0
                self.progress_bar.start(10)  # Start indeterminate animation
                time.sleep(0.1)
            else:
                break
                
    def show(self, status: str = "Processing..."):
        """
        Show the loader window with the given status.
        
        Args:
            status: Status message to display
        """
        if self.is_running:
            self.update_status(status)
            return
            
        self.is_running = True
        self.stop_animation = False
        
        # Create window on main thread to avoid Tkinter threading issues
        self._create_loader_window()
        self.update_status(status)
        self.progress_bar.start(10)  # Start indeterminate animation
        
        # Start mainloop in a separate thread to avoid blocking
        def run_mainloop():
            self.root.mainloop()
            
        self.animation_thread = threading.Thread(target=run_mainloop, daemon=True)
        self.animation_thread.start()
        
        # Small delay to ensure window is created
        time.sleep(0.1)
        
    def update_status(self, status: str):
        """
        Update the status message.
        
        Args:
            status: New status message
        """
        if self.status_var and self.root:
            try:
                # Schedule the update on the main thread
                self.root.after(0, lambda: self.status_var.set(status))
            except:
                pass  # Ignore if window is being destroyed
            
    def update_progress(self, progress: int, status: str = None):
        """
        Update progress percentage and optionally status.
        
        Args:
            progress: Progress percentage (0-100)
            status: Optional status message
        """
        if self.root:
            try:
                # Schedule the update on the main thread
                if self.progress_var:
                    self.root.after(0, lambda: self.progress_var.set(f"{progress}%"))
                    
                if status and self.status_var:
                    self.root.after(0, lambda: self.status_var.set(status))
            except:
                pass  # Ignore if window is being destroyed
            
        # Switch to determinate mode for specific progress
        if self.progress_bar and progress >= 0:
            self.progress_bar.stop()
            self.progress_bar['mode'] = 'determinate'
            self.progress_bar['value'] = progress
            
    def hide(self):
        """Hide the loader window."""
        self.is_running = False
        self.stop_animation = True
        
        if self.root:
            try:
                # Stop progress bar first
                if self.progress_bar:
                    self.progress_bar.stop()
                    
                # Clear variables to prevent cleanup issues
                if self.progress_var:
                    self.progress_var = None
                if self.status_var:
                    self.status_var = None
                    
                # Properly quit and destroy
                self.root.quit()
                self.root.destroy()
            except Exception:
                pass
            finally:
                self.root = None
                self.progress_bar = None
            
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1)
            
    def is_visible(self) -> bool:
        """Check if the loader is currently visible."""
        return self.is_running and self.root is not None


class LoaderManager:
    """
    Manager class for handling loader instances and integration with agent execution.
    """
    
    def __init__(self):
        self.loader: Optional[DesktopLoader] = None
        self.is_enabled = True
        # Register cleanup function to run on program exit
        atexit.register(self.cleanup)
        
    def start_loader(self, status: str = "Starting task..."):
        """Start the loader with initial status."""
        if not self.is_enabled:
            return
            
        if self.loader is None:
            self.loader = DesktopLoader()
            
        self.loader.show(status)
        
    def update_loader(self, status: str, progress: Optional[int] = None):
        """Update loader status and optionally progress."""
        if not self.is_enabled or not self.loader:
            return
            
        if progress is not None:
            self.loader.update_progress(progress, status)
        else:
            self.loader.update_status(status)
            
    def stop_loader(self):
        """Stop and hide the loader."""
        if self.loader:
            self.loader.hide()
            self.loader = None
            
    def set_enabled(self, enabled: bool):
        """Enable or disable the loader."""
        self.is_enabled = enabled
        if not enabled and self.loader:
            self.stop_loader()
            
    def is_loader_visible(self) -> bool:
        """Check if loader is currently visible."""
        return self.loader is not None and self.loader.is_visible()
        
    def cleanup(self):
        """Cleanup method called on program exit to prevent tkinter exceptions."""
        if self.loader:
            try:
                self.loader.hide()
            except Exception:
                pass
            self.loader = None
