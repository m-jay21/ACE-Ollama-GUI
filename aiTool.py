import re
import ollama
import json
import tiktoken
import os
import subprocess
import time
import sys

def get_messages_file_path():
    if getattr(sys, 'frozen', False):
        # Running in a bundle (packaged app)
        base_path = os.path.dirname(sys.executable)
        return os.path.join(base_path, 'resources', 'theMessages.txt')
    else:
        # Running in normal Python environment
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'theMessages.txt')

def aiOptions():
    response = ollama.list()
    model_names = [model["model"] for model in response["models"]]
    return model_names

def cleanAnsi(text):
    #removes any ansi characters and spinning values that ollama outputs
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    spinner_artifacts = re.compile(r'[⠋⠙⠹⠼⠧⠇⠏⠸⠴⠦⠬⠰⠾⠶⠖⠆⠖⠲]+')
    text = ansi_escape.sub('', text)
    text = spinner_artifacts.sub('', text)
    #keeps a space after punctuation if needed.
    text = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', text)
    return text

def format_time(seconds):
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"

def downloadModel(model_name):
    if model_name in aiOptions():
        print(json.dumps({"status": "Already Installed", "progress": 100}))
        sys.stdout.flush()
        return
    try:
        start_time = time.time()
        last_progress = 0
        process = subprocess.Popen(
            ['ollama', 'pull', model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                # Extract percentage from any line
                match = re.search(r'(\d+)%', line)
                if match:
                    current_progress = int(match.group(1))
                    last_progress = current_progress
                else:
                    current_progress = last_progress
                # Time estimate
                elapsed = time.time() - start_time
                if current_progress > 0 and current_progress < 100:
                    est_total = elapsed / (current_progress / 100)
                    est_remaining = est_total - elapsed
                    if est_remaining > 60:
                        mins = int(est_remaining // 60)
                        secs = int(est_remaining % 60)
                        time_estimate = f" (Est. {mins}m {secs}s left)"
                    else:
                        time_estimate = f" (Est. {int(est_remaining)}s left)"
                else:
                    time_estimate = ""
                print(json.dumps({
                    "status": f"{line.strip()}{time_estimate}",
                    "progress": current_progress
                }))
                sys.stdout.flush()
        if process.returncode == 0:
            print(json.dumps({"status": "Installed", "progress": 100}))
            sys.stdout.flush()
        else:
            print(json.dumps({"status": "Cannot be installed", "progress": 0}))
            sys.stdout.flush()
    except Exception:
        print(json.dumps({"status": "Cannot be installed", "progress": 0}))
        sys.stdout.flush()

#estimate tokens in a list of messages
def estimate_tokens(message):
    enc = tiktoken.get_encoding("cl100k_base")
    total_tokens = sum(len(enc.encode(msg["content"])) for msg in message)
    return total_tokens

#calculate num_ctx
def get_dynamic_num_ctx(message):
    token_count = estimate_tokens(message)

    if token_count <= 2048:
        return 2048
    elif token_count <= 4096:
        return 4096
    elif token_count <= 8192:
        return 8192
    else:
        print("Input exceeds max limit.")
        return 8192  #max possible limit

def runData(text, model):
    messages_file = get_messages_file_path()
    
    #append user message
    with open(messages_file, 'a') as file:
        file.write(json.dumps({"role": "user", "content": text}) + "\n")

    #open the file for reading
    with open(messages_file, 'r') as file:
        lines = file.readlines() 
        theMessages = [json.loads(line.strip()) for line in lines if line.strip()]  #convert JSON strings to dicts

    num_ctx = get_dynamic_num_ctx(theMessages)

    #send messages to Ollama
    stream = ollama.chat(model=model, messages=theMessages, stream=True, options={"num_ctx": num_ctx})

    full_response = ""

    for chunk in stream:
        word = chunk.get('message', {}).get('content', '')
        full_response += word
        yield word  #yield word-by-word

    #append assistant response properly
    with open(messages_file, 'a') as file:
        file.write(json.dumps({"role": "assistant", "content": full_response}) + "\n")

def runImage(text, imagePath):
    messages_file = get_messages_file_path()
    
    # Get the list of installed models
    model_names = aiOptions()

    if "llava:latest" not in model_names:
        message = "Llava model required for image processing.\nPlease install it in the settings tab."
        for word in message.split():
            yield word + " "
        return

    # Ensure the image path is absolute
    imagePath = os.path.abspath(imagePath)

    if not os.path.exists(imagePath):
        yield "Error: The provided image path does not exist."
        return

    # Run the model with image processing
    stream = ollama.generate(
        model="llava",
        prompt=text,
        images=[imagePath],
        stream=True  
    )

    full_response = ""
    for chunk in stream:
        word = chunk.get("response", "") 
        full_response += word
        yield word  

    # Store the full response
    with open(messages_file, 'a') as file:
        file.write(json.dumps({"role": "assistant", "content": full_response}) + "\n")

