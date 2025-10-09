"""
Build script for packaging the Python backend into a standalone executable.
Uses PyInstaller to create a single executable file.
"""

import PyInstaller.__main__
import os
import sys
import shutil
import subprocess

def check_and_fix_dependencies():
    """Check for and fix common PyInstaller compatibility issues."""
    
    # Remove enum34 if present (incompatible with PyInstaller)
    try:
        print("Checking for incompatible packages...")
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "enum34", "-y"],
            capture_output=True,
            check=False
        )
        print("✅ Environment check passed")
    except Exception as e:
        print(f"Warning: Could not check dependencies: {e}")

def build_backend():
    """Build the backend using PyInstaller."""
    
    # Check and fix dependencies first
    check_and_fix_dependencies()
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_script = os.path.join(project_root, 'api_server.py')
    
    if not os.path.exists(backend_script):
        print(f"Error: Backend script not found at {backend_script}")
        sys.exit(1)
    
    print("Building backend executable...")
    print(f"Project root: {project_root}")
    print(f"Backend script: {backend_script}")
    
    pyinstaller_args = [
        backend_script,
        '--name=api_server',
        '--onefile',
        '--clean',
        f'--distpath={os.path.join(project_root, "desktop-app", "backend")}',
        f'--workpath={os.path.join(project_root, "desktop-app", "build")}',
        f'--specpath={os.path.join(project_root, "desktop-app")}',
        '--hidden-import=windows_use',
        '--hidden-import=windows_use.agent',
        '--hidden-import=windows_use.desktop',
        '--hidden-import=windows_use.tree',
        '--hidden-import=langchain_google_genai',
        '--hidden-import=fastapi',
        '--hidden-import=uvicorn',
        '--hidden-import=pydantic',
        '--hidden-import=dotenv',
        '--hidden-import=google.generativeai',
        '--hidden-import=google.ai.generativelanguage',
        '--collect-all=windows_use',
        '--collect-all=langchain_google_genai',
        '--collect-all=google.generativeai',
        '--console',  # Show console for debugging; change to --noconsole for production
        f'--add-data={os.path.join(project_root, "windows_use")};windows_use',
    ]
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("\n✅ Backend build completed successfully!")
        print(f"Executable location: {os.path.join(project_root, 'desktop-app', 'backend', 'api_server.exe')}")
    except Exception as e:
        print(f"\n❌ Backend build failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build_backend()

