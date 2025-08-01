#!/usr/bin/env python3
import sys
import os
import json

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from ai_tool import deleteModel

if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            print(json.dumps({"status": "error", "message": "Model name not provided"}))
            sys.exit(1)
        
        model_name = sys.argv[1]
        result = deleteModel(model_name)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1) 