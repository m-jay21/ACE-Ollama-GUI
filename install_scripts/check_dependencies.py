#!/usr/bin/env python3
"""
Dependency checker and installer for ACE's Local AI
This script checks for required dependencies and installs them if needed.
"""

import sys
import os
import subprocess
import importlib
import json
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or later is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_pip():
    """Check if pip is available"""
    try:
        import pip
        print("✓ pip is available")
        return True
    except ImportError:
        print("ERROR: pip is not available")
        return False

def get_requirements_path():
    """Get the path to requirements.txt"""
    if getattr(sys, 'frozen', False):
        # Running in a bundle (packaged app)
        base_path = os.path.dirname(sys.executable)
        if platform.system() == "Darwin":  # macOS
            base_path = os.path.join(base_path, "..", "Resources")
        return os.path.join(base_path, "requirements.txt")
    else:
        # Development mode
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt")

def install_requirements():
    """Install Python requirements"""
    requirements_path = get_requirements_path()
    
    if not os.path.exists(requirements_path):
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        return False
    
    print(f"Installing requirements from {requirements_path}")
    
    try:
        # Use subprocess to install requirements
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Requirements installed successfully")
            return True
        else:
            print(f"ERROR: Failed to install requirements: {result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to install requirements: {e}")
        return False

def check_ollama():
    """Check if Ollama is installed and running"""
    try:
        # Try to connect to Ollama
        import requests
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama is running")
            return True
    except:
        pass
    
    print("⚠ Ollama is not running or not installed")
    return False

def check_key_dependencies():
    """Check if key dependencies are available"""
    key_deps = [
        "ollama",
        "pymupdf", 
        "pillow",
        "tiktoken",
        "langchain",
        "sentence_transformers",
        "faiss",
        "numpy"
    ]
    
    missing_deps = []
    
    for dep in key_deps:
        try:
            importlib.import_module(dep)
            print(f"✓ {dep} is available")
        except ImportError:
            print(f"✗ {dep} is missing")
            missing_deps.append(dep)
    
    return len(missing_deps) == 0, missing_deps

def create_app_data_directory():
    """Create application data directory"""
    if platform.system() == "Windows":
        app_data = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ACE-AI")
    elif platform.system() == "Darwin":  # macOS
        app_data = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "ACE-AI")
    else:  # Linux
        app_data = os.path.join(os.path.expanduser("~"), ".ace_ai")
    
    os.makedirs(app_data, exist_ok=True)
    print(f"✓ App data directory created: {app_data}")
    return app_data

def main():
    """Main dependency check and installation function"""
    print("ACE's Local AI - Dependency Checker")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check pip
    if not check_pip():
        return False
    
    # Create app data directory
    app_data = create_app_data_directory()
    
    # Check if key dependencies are available
    deps_ok, missing_deps = check_key_dependencies()
    
    if not deps_ok:
        print(f"\nInstalling missing dependencies: {', '.join(missing_deps)}")
        if not install_requirements():
            return False
    
    # Check Ollama
    ollama_ok = check_ollama()
    
    # Create status file
    status = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "dependencies_ok": deps_ok,
        "ollama_ok": ollama_ok,
        "app_data_dir": app_data,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }
    
    status_file = os.path.join(app_data, "dependency_status.json")
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"\n✓ Dependency check completed. Status saved to: {status_file}")
    
    if not ollama_ok:
        print("\n⚠ Please install Ollama from https://ollama.ai and run 'ollama serve'")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
