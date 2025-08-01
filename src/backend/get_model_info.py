#!/usr/bin/env python3
import sys
import os
import json

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from ai_tool import getModelInfo

if __name__ == "__main__":
    try:
        model_info = getModelInfo()
        print(json.dumps(model_info))
    except Exception as e:
        print(json.dumps([]))
        sys.exit(1) 