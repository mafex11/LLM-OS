"""
Build script for packaging the Python backend into a standalone executable.
Uses PyInstaller to create a single executable file with minimal dependencies.
"""

import PyInstaller.__main__
import os
import sys
import subprocess

def check_and_fix_dependencies():
    """Check for and fix common PyInstaller compatibility issues."""
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
    """Build the backend using PyInstaller with optimized settings."""
    
    check_and_fix_dependencies()
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_script = os.path.join(project_root, 'api_server.py')
    
    if not os.path.exists(backend_script):
        print(f"Error: Backend script not found at {backend_script}")
        sys.exit(1)
    
    print("Building backend executable with optimized settings...")
    print(f"Project root: {project_root}")
    print(f"Backend script: {backend_script}")
    
    # Exclude unnecessary large packages to reduce size
    exclude_packages = [
        'torch', 'torchaudio', 'torchvision',  # ML frameworks
        'tensorflow', 'keras',
        'sklearn', 'scipy',  # Scientific computing
        'IPython', 'jupyter',  # Interactive shells
        'matplotlib',  # Plotting
        'PIL.PngImagePlugin',  # Keep PIL but not all plugins
        'selenium',  # Browser automation (not needed)
        'scrapy',  # Web scraping
        'twisted',  # Async framework
        'zmq',  # ZeroMQ
        'pandas',  # Data analysis
    ]
    
    pyinstaller_args = [
        backend_script,
        '--name=api_server',
        '--onefile',
        '--clean',
        f'--distpath={os.path.join(project_root, "desktop-app", "backend")}',
        f'--workpath={os.path.join(project_root, "desktop-app", "build")}',
        f'--specpath={os.path.join(project_root, "desktop-app")}',
        # Essential hidden imports
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
        '--hidden-import=langchain_core',
        '--hidden-import=langgraph',
        '--hidden-import=live_inspect',
        # Exclude massive packages
    ]
    
    # Add exclusions
    for package in exclude_packages:
        pyinstaller_args.append(f'--exclude-module={package}')
    
    # Add data files
    pyinstaller_args.extend([
        '--collect-all=windows_use',
        '--collect-all=langchain_google_genai',
        '--collect-all=google.generativeai',
        '--console',  # Keep console for debugging
    ])
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("\n✅ Backend build completed successfully!")
        print(f"Executable location: {os.path.join(project_root, 'desktop-app', 'backend', 'api_server.exe')}")
    except Exception as e:
        print(f"\n❌ Backend build failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build_backend()

