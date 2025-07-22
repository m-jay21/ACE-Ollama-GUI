import argparse
from ai_tool import downloadModel

def main():
    parser = argparse.ArgumentParser(description="Download a model if not already installed.")
    parser.add_argument('--model', type=str, required=True, help="The model name to download")
    
    args = parser.parse_args()
    result = downloadModel(args.model)
    print(result, flush=True)

if __name__ == "__main__":
    main()
