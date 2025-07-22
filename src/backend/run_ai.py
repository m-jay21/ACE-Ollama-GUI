import argparse
import os
from ai_tool import runData, runImage
import pdf_tool

def main():
    parser = argparse.ArgumentParser(description="Process AI Query with optional file input.")
    parser.add_argument('--query', type=str, required=True, help="The user query text")
    parser.add_argument('--model', type=str, required=True, help="The AI model to use")
    parser.add_argument('--file', type=str, default="", help="Optional file path (PDF or image)")
    
    args = parser.parse_args()
    query = args.query
    file_path = args.file.strip()

    if file_path:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            # Extract PDF text and prepend it to the query
            pdf_text = pdf_tool.extract_text_from_pdf(file_path)
            query = "PDF TEXT:\n" + pdf_text + "\nUSER QUERY:\n" + query
            # Process as a text-based query
            for word in runData(query, args.model):
                print(word, end='', flush=True)
        elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
            # Process as an image-based query
            for word in runImage(query, file_path):
                print(word, end='', flush=True)
        else:
            print("Unsupported file type.", flush=True)
    else:
        # No file provided; process as a normal text query.
        for word in runData(query, args.model):
            print(word, end='', flush=True)

if __name__ == "__main__":
    main()
