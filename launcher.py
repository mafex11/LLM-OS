"""
Windows-Use Launcher

Choose between GUI mode or command-line mode.
"""

import sys
import os

def show_menu():
    """Show the launcher menu."""
    print("🤖 Windows-Use Agent Launcher")
    print("=" * 40)
    print("1. GUI Mode (Windows Interface)")
    print("2. Command Line Mode (Terminal)")
    print("3. Exit")
    print("=" * 40)

def run_gui():
    """Run the GUI application."""
    try:
        print("🚀 Starting GUI application...")
        from gui_app import main
        main()
    except ImportError as e:
        print(f"❌ Error importing GUI: {e}")
        print("Make sure tkinter is installed (usually comes with Python)")
        input("Press Enter to continue...")
    except Exception as e:
        print(f"❌ Error running GUI: {e}")
        input("Press Enter to continue...")

def run_cli():
    """Run the command line application."""
    try:
        print("🚀 Starting command line application...")
        from main import main as cli_main
        cli_main()
    except Exception as e:
        print(f"❌ Error running CLI: {e}")
        input("Press Enter to continue...")

def main():
    """Main launcher function."""
    while True:
        try:
            show_menu()
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == '1':
                run_gui()
            elif choice == '2':
                run_cli()
            elif choice == '3':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
