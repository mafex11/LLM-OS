"""
Yuki AI GUI Application

A native Windows GUI for the Yuki AI agent system using tkinter.
Provides a clean interface for entering queries and viewing responses.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import sys
import os
from datetime import datetime
import ctypes

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from windows_use.agent.service import Agent
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from main import get_running_programs, display_running_programs

class WindowsUseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Yuki AI Agent")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Initialize agent
        self.agent = None
        self.response_queue = queue.Queue()
        self.is_processing = False
        self.overlay_window = None
        self.overlay_message_var = tk.StringVar(value="Working...")
        
        # Setup GUI
        self.setup_gui()
        self.initialize_agent()
        
        # Start response processing
        self.process_responses()

        # Ensure overlay stays on top when root is minimized/restored
        self.root.bind('<Unmap>', self._on_root_minimize)
        self.root.bind('<Map>', self._on_root_restore)
    
    def setup_gui(self):
        """Setup the GUI layout and components."""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="LLM OS", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Query input frame
        query_frame = ttk.LabelFrame(main_frame, text="Enter Your Query", padding="10")
        query_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        query_frame.columnconfigure(0, weight=1)
        
        # Query entry
        self.query_var = tk.StringVar()
        self.query_entry = ttk.Entry(query_frame, textvariable=self.query_var, font=('Arial', 11))
        self.query_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.query_entry.bind('<Return>', self.on_submit)
        self.query_entry.bind('<Control-Return>', self.on_submit)
        
        # Submit button
        self.submit_btn = ttk.Button(query_frame, text="Submit", command=self.on_submit)
        self.submit_btn.grid(row=0, column=1)
        
        # Response area
        response_frame = ttk.LabelFrame(main_frame, text="Agent Response", padding="10")
        response_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        response_frame.columnconfigure(0, weight=1)
        response_frame.rowconfigure(0, weight=1)
        
        # Response text area
        self.response_text = scrolledtext.ScrolledText(
            response_frame, 
            wrap=tk.WORD, 
            font=('Consolas', 10),
            height=20,
            state=tk.DISABLED
        )
        self.response_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))
        
        # Control buttons frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Control buttons
        ttk.Button(controls_frame, text="Clear", command=self.clear_response).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(controls_frame, text="Settings", command=self.show_settings).grid(row=0, column=1, padx=5)
        ttk.Button(controls_frame, text="Performance", command=self.show_performance).grid(row=0, column=2, padx=5)
        ttk.Button(controls_frame, text="Exit", command=self.on_closing).grid(row=0, column=3, padx=(5, 0))
        
        # Focus on query entry
        self.query_entry.focus()

    # ----------------------------
    # Overlay (Always-on-top) UI
    # ----------------------------
    def _create_overlay_if_needed(self):
        """Create a small always-on-top overlay window if it doesn't exist."""
        if self.overlay_window and self.overlay_window.winfo_exists():
            return

        ow = tk.Toplevel(self.root)
        self.overlay_window = ow
        ow.overrideredirect(True)  # borderless
        try:
            ow.wm_attributes('-topmost', True)
            ow.wm_attributes('-alpha', 0.95)
            # On Windows, toolwindow hides from taskbar and alt-tab
            ow.wm_attributes('-toolwindow', True)
        except Exception:
            pass

        # Content
        frame = ttk.Frame(ow, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        status_label = ttk.Label(frame, textvariable=self.overlay_message_var, font=('Segoe UI', 10, 'bold'))
        status_label.pack(side=tk.LEFT, padx=(0, 8))

        self.overlay_progress = ttk.Progressbar(frame, mode='indeterminate', length=120)
        self.overlay_progress.pack(side=tk.LEFT)

        # Position bottom-right by default
        self._position_overlay_bottom_right()

    def _position_overlay_bottom_right(self):
        """Position the overlay at bottom-right of the current display."""
        if not (self.overlay_window and self.overlay_window.winfo_exists()):
            return
        ow = self.overlay_window
        ow.update_idletasks()
        width = ow.winfo_width()
        height = ow.winfo_height()
        # Use screen geometry (primary monitor)
        screen_w = ow.winfo_screenwidth()
        screen_h = ow.winfo_screenheight()
        x = screen_w - width - 20
        y = screen_h - height - 60
        ow.geometry(f"{width}x{height}+{x}+{y}")

    def show_overlay(self, message: str = "Working..."):
        """Show the overlay and keep it on top."""
        self._create_overlay_if_needed()
        self.overlay_message_var.set(message)
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.deiconify()
            try:
                self.overlay_window.wm_attributes('-topmost', True)
            except Exception:
                pass
            self._position_overlay_bottom_right()
            try:
                self.overlay_progress.start(10)
            except Exception:
                pass

    def hide_overlay(self):
        """Hide the overlay and stop its progress bar."""
        if self.overlay_window and self.overlay_window.winfo_exists():
            try:
                self.overlay_progress.stop()
            except Exception:
                pass
            self.overlay_window.withdraw()

    def _on_root_minimize(self, event=None):
        """When root minimizes, keep overlay visible independently if processing."""
        if self.is_processing:
            self.show_overlay("Working...")

    def _on_root_restore(self, event=None):
        """On restore, ensure overlay remains topmost if processing, else hide it."""
        if self.is_processing:
            self.show_overlay("Working...")
        else:
            self.hide_overlay()
    
    def initialize_agent(self):
        """Initialize the Windows-Use agent in a separate thread."""
        def init_agent():
            try:
                # Ensure COM is initialized for UIAutomation in this thread
                try:
                    ctypes.windll.ole32.CoInitializeEx(0, 2)  # COINIT_APARTMENTTHREADED
                except Exception:
                    pass
                self.update_status("Initializing agent...")
                
                # Get running programs
                running_programs = get_running_programs()
                
                # Initialize LLM - prefer DeepSeek over Gemini
                deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
                
                if deepseek_api_key:
                    llm = ChatOpenAI(
                        model="deepseek-chat",
                        temperature=0.3,
                        openai_api_key=deepseek_api_key,
                        openai_api_base="https://api.deepseek.com"
                    )
                else:
                    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
                self.agent = Agent(
                    llm=llm, 
                    browser='chrome', 
                    use_vision=False, 
                    enable_conversation=True, 
                    literal_mode=True, 
                    max_steps=30
                )
                
                # Store running programs in agent
                self.agent.running_programs = running_programs
                
                # Pre-warm the system (DISABLED)
                # self.update_status("Pre-warming system...")
                # try:
                #     self.agent.desktop.get_state(use_vision=False)
                #     self.update_status("System pre-warmed successfully!")
                # except Exception as e:
                #     self.update_status(f"Pre-warming failed: {e}")
                
                self.update_status("Ready - Enter your query above")
                self.add_response("🤖 Yuki AI Agent initialized successfully!")
                self.add_response("📱 Detected running programs:")
                
                # Display running programs
                if running_programs:
                    grouped = {}
                    for prog in running_programs:
                        name = prog['name']
                        if name not in grouped:
                            grouped[name] = []
                        grouped[name].append(prog)
                    
                    for name, instances in grouped.items():
                        self.add_response(f"• {name.title()}")
                        for instance in instances:
                            if instance['title'] and instance['title'] != name:
                                self.add_response(f"  - {instance['title']}")
                else:
                    self.add_response("No programs with visible windows detected")
                
                self.add_response("\n" + "="*50)
                self.add_response("Ready for your commands!")
                
            except Exception as e:
                self.update_status(f"Initialization failed: {e}")
                self.add_response(f"❌ Error initializing agent: {e}")
        
        # Run initialization in background thread
        threading.Thread(target=init_agent, daemon=True).start()
    
    def on_submit(self, event=None):
        """Handle query submission."""
        if self.is_processing:
            messagebox.showwarning("Processing", "Please wait for the current query to complete.")
            return
        
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("Empty Query", "Please enter a query.")
            return
        
        if not self.agent:
            messagebox.showerror("Not Ready", "Agent is still initializing. Please wait.")
            return
        
        # Clear query entry
        self.query_var.set("")
        
        # Start processing in background thread
        self.is_processing = True
        self.submit_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.update_status("Processing query...")
        self.show_overlay("Processing your task...")
        
        def process_query():
            try:
                # Ensure COM is initialized for UIAutomation in this worker thread
                try:
                    ctypes.windll.ole32.CoInitializeEx(0, 2)
                except Exception:
                    pass
                self.add_response(f"\n💬 You: {query}")
                self.add_response("🔄 Processing...")
                
                # Process the query
                response = self.agent.invoke(query)
                
                # Add response to queue
                self.response_queue.put(('response', response.content or response.error))
                
            except Exception as e:
                self.response_queue.put(('error', f"Error processing query: {e}"))
            finally:
                self.response_queue.put(('done', None))
        
        threading.Thread(target=process_query, daemon=True).start()
    
    def process_responses(self):
        """Process responses from the background thread."""
        try:
            while True:
                msg_type, content = self.response_queue.get_nowait()
                
                if msg_type == 'response':
                    self.add_response(f"\n🤖 Agent: {content}")
                elif msg_type == 'error':
                    self.add_response(f"\n❌ Error: {content}")
                elif msg_type == 'done':
                    self.is_processing = False
                    self.submit_btn.config(state=tk.NORMAL)
                    self.progress.stop()
                    self.update_status("Ready - Enter your next query")
                    self.hide_overlay()
                    self.query_entry.focus()
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_responses)
    
    def add_response(self, text):
        """Add text to the response area."""
        self.response_text.config(state=tk.NORMAL)
        self.response_text.insert(tk.END, text + "\n")
        self.response_text.see(tk.END)
        self.response_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def clear_response(self):
        """Clear the response area."""
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete(1.0, tk.END)
        self.response_text.config(state=tk.DISABLED)
    
    def update_status(self, text):
        """Update the status label."""
        self.status_var.set(text)
        self.root.update_idletasks()
    
    def show_settings(self):
        """Show settings dialog."""
        if not self.agent:
            messagebox.showwarning("Not Ready", "Agent is not initialized yet.")
            return
        
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Settings frame
        settings_frame = ttk.Frame(settings_window, padding="20")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Detection settings
        ttk.Label(settings_frame, text="Detection Settings", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Adaptive detection (guard missing attributes)
        has_adaptive = hasattr(self.agent.desktop, 'use_adaptive_detection') and hasattr(self.agent.desktop, 'set_adaptive_detection')
        adaptive_initial = getattr(self.agent.desktop, 'use_adaptive_detection', False)
        adaptive_var = tk.BooleanVar(value=adaptive_initial)
        adaptive_cb = ttk.Checkbutton(settings_frame, text="Enable Adaptive Detection", 
                       variable=adaptive_var, 
                       command=(lambda: self.agent.desktop.set_adaptive_detection(adaptive_var.get())) if has_adaptive else None)
        adaptive_cb.state(['!disabled'] if has_adaptive else ['disabled'])
        adaptive_cb.pack(anchor=tk.W, pady=2)
        
        # Intelligent detection (guard missing attributes)
        has_intelligent = hasattr(self.agent.desktop, 'use_intelligent_detection') and hasattr(self.agent.desktop, 'set_intelligent_detection')
        intelligent_initial = getattr(self.agent.desktop, 'use_intelligent_detection', False)
        intelligent_var = tk.BooleanVar(value=intelligent_initial)
        intelligent_cb = ttk.Checkbutton(settings_frame, text="Enable Intelligent Detection", 
                       variable=intelligent_var,
                       command=(lambda: self.agent.desktop.set_intelligent_detection(intelligent_var.get())) if has_intelligent else None)
        intelligent_cb.state(['!disabled'] if has_intelligent else ['disabled'])
        intelligent_cb.pack(anchor=tk.W, pady=2)
        
        # Speed optimizations
        speed_var = tk.BooleanVar(value=self.agent.desktop.cache_timeout == 1.0)
        ttk.Checkbutton(settings_frame, text="Enable Speed Optimizations", 
                       variable=speed_var,
                       command=lambda: self.toggle_speed_optimizations(speed_var.get())).pack(anchor=tk.W, pady=2)
        
        # Close button
        ttk.Button(settings_frame, text="Close", command=settings_window.destroy).pack(pady=(20, 0))
    
    def toggle_speed_optimizations(self, enabled):
        """Toggle speed optimizations."""
        if enabled:
            self.agent.desktop.cache_timeout = 1.0
            self.agent.desktop.clear_cache()
        else:
            self.agent.desktop.cache_timeout = 0.1
    
    def show_performance(self):
        """Show performance statistics."""
        if not self.agent:
            messagebox.showwarning("Not Ready", "Agent is not initialized yet.")
            return
        
        perf_window = tk.Toplevel(self.root)
        perf_window.title("Performance Statistics")
        perf_window.geometry("500x400")
        perf_window.transient(self.root)
        perf_window.grab_set()
        
        # Performance frame
        perf_frame = ttk.Frame(perf_window, padding="20")
        perf_frame.pack(fill=tk.BOTH, expand=True)
        
        # Performance text
        perf_text = scrolledtext.ScrolledText(perf_frame, wrap=tk.WORD, font=('Consolas', 9))
        perf_text.pack(fill=tk.BOTH, expand=True)
        
        # Get performance stats
        try:
            perf_text.insert(tk.END, "📊 Performance Statistics\n")
            perf_text.insert(tk.END, "=" * 50 + "\n\n")
            
            # Agent performance stats
            if hasattr(self.agent, 'performance_monitor'):
                stats = self.agent.performance_monitor.get_stats()
                if stats:
                    perf_text.insert(tk.END, "Agent Performance:\n")
                    for operation, data in stats.items():
                        perf_text.insert(tk.END, f"  {operation}:\n")
                        perf_text.insert(tk.END, f"    Count: {data['count']}\n")
                        perf_text.insert(tk.END, f"    Avg Time: {data['avg_time']:.3f}s\n")
                        perf_text.insert(tk.END, f"    Total Time: {data['total_time']:.3f}s\n\n")
                else:
                    perf_text.insert(tk.END, "No performance data available yet.\n\n")
            
            # Detection system stats
            detection_stats = self.agent.desktop.get_detection_stats()
            perf_text.insert(tk.END, "Detection System:\n")
            for key, value in detection_stats.items():
                perf_text.insert(tk.END, f"  {key}: {value}\n")
            
        except Exception as e:
            perf_text.insert(tk.END, f"Error getting performance stats: {e}")
        
        perf_text.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(perf_frame, text="Close", command=perf_window.destroy).pack(pady=(10, 0))
    
    def on_closing(self):
        """Handle application closing."""
        if self.is_processing:
            if messagebox.askokcancel("Quit", "A query is currently processing. Are you sure you want to quit?"):
                try:
                    self.hide_overlay()
                except Exception:
                    pass
                self.root.destroy()
        else:
            try:
                self.hide_overlay()
            except Exception:
                pass
            self.root.destroy()

def main():
    """Main function to run the GUI application."""
    root = tk.Tk()
    app = WindowsUseGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()
