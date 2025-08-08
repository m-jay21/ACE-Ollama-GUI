#!/usr/bin/env python3
"""
Python installer for ACE's Local AI
This script helps users install Python dependencies
"""

import sys
import subprocess
import os

def install_requirements():
    """Install Python requirements"""
    try:
        # Get the path to requirements.txt
        if getattr(sys, 'frozen', False):
            # Running in a bundle
            base_path = os.path.dirname(sys.executable)
            if os.name == 'nt':  # Windows
                base_path = os.path.join(base_path, '..', 'Resources')
            requirements_path = os.path.join(base_path, 'requirements.txt')
        else:
            # Development mode
            requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
        
        if not os.path.exists(requirements_path):
            print(f"ERROR: requirements.txt not found at {requirements_path}")
            return False
        
        print(f"Installing requirements from {requirements_path}")
        
        # Install requirements
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', requirements_path
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

if __name__ == "__main__":
    success = install_requirements()
    sys.exit(0 if success else 1)
