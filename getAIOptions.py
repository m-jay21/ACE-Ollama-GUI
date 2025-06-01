import json
import sys
from aiTool import aiOptions

def main():
    try:
        options = aiOptions()
        if not options:  # If no models are found
            options = ["No models found"]  # Show message instead of default model
        print(json.dumps(options))
    except Exception as e:
        print(json.dumps(["No models found"]))  # Show message on error
        sys.exit(1)

if __name__ == "__main__":
    main()
