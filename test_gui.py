"""
Test script for the GUI application
"""

import tkinter as tk
from tkinter import messagebox

def test_gui():
    """Test the GUI without full agent initialization."""
    root = tk.Tk()
    root.title("GUI Test")
    root.geometry("400x300")
    
    # Test basic GUI components
    label = tk.Label(root, text="GUI Test - Basic Components Working", font=('Arial', 14))
    label.pack(pady=20)
    
    # Test button
    def test_button():
        messagebox.showinfo("Test", "Button click works!")
    
    button = tk.Button(root, text="Test Button", command=test_button)
    button.pack(pady=10)
    
    # Test entry
    entry = tk.Entry(root, width=30)
    entry.pack(pady=10)
    entry.insert(0, "Test entry field")
    
    # Test text area
    text_area = tk.Text(root, height=5, width=40)
    text_area.pack(pady=10)
    text_area.insert(tk.END, "Test text area\nLine 2\nLine 3")
    
    # Close button
    close_btn = tk.Button(root, text="Close", command=root.destroy)
    close_btn.pack(pady=10)
    
    print("✅ GUI test window opened successfully!")
    print("If you can see the window and interact with it, the GUI is working!")
    
    root.mainloop()

if __name__ == "__main__":
    test_gui()
