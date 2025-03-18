import json
from aiTool import aiOptions

def main():
    options = aiOptions()
    print(json.dumps(options))

if __name__ == "__main__":
    main()
