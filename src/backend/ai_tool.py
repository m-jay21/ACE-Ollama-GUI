import re
import ollama
import json
import tiktoken
import os
import subprocess
import time
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_messages_file_path():
    if getattr(sys, 'frozen', False):
        # Running in a bundle (packaged app)
        base_path = os.path.dirname(sys.executable)
        messages_path = os.path.join(base_path, 'resources', 'src', 'data', 'theMessages.txt')
    else:
        # Running in normal Python environment - go up one level from backend to src, then to data
        messages_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'theMessages.txt')
    
    # Ensure the data directory exists
    data_dir = os.path.dirname(messages_path)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    return messages_path

def validate_input(text, max_length=50000):
    """Validate and sanitize input text"""
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    if len(text) > max_length:
        raise ValueError(f"Input too long. Maximum length is {max_length} characters")
    
    # Remove null bytes and other dangerous characters
    text = text.replace('\x00', '')
    
    return text.strip()

def validate_model_name(model_name):
    """Validate model name format"""
    if not isinstance(model_name, str):
        raise ValueError("Model name must be a string")
    
    # Only allow alphanumeric characters, hyphens, underscores, and colons
    if not re.match(r'^[a-zA-Z0-9\-_:]+$', model_name):
        raise ValueError("Invalid model name format")
    
    return model_name.strip()

def aiOptions():
    try:
        response = ollama.list()
        model_names = [model["model"] for model in response["models"]]
        return model_names
    except Exception as e:
        logger.error(f"Error getting AI options: {e}")
        return []

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
    try:
        # Validate model name
        model_name = validate_model_name(model_name)
        
        if model_name in aiOptions():
            print(json.dumps({"status": "Already Installed", "progress": 100}))
            sys.stdout.flush()
            return
        
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
    except Exception as e:
        logger.error(f"Error downloading model {model_name}: {e}")
        print(json.dumps({"status": "Cannot be installed", "progress": 0}))
        sys.stdout.flush()

#estimate tokens in a list of messages
def estimate_tokens(message):
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        total_tokens = sum(len(enc.encode(msg["content"])) for msg in message)
        return total_tokens
    except Exception as e:
        logger.error(f"Error estimating tokens: {e}")
        return 0

#calculate num_ctx
def get_dynamic_num_ctx(message):
    try:
        token_count = estimate_tokens(message)

        if token_count <= 2048:
            return 2048
        elif token_count <= 4096:
            return 4096
        elif token_count <= 8192:
            return 8192
        else:
            logger.warning("Input exceeds max limit.")
            return 8192  #max possible limit
    except Exception as e:
        logger.error(f"Error calculating dynamic context: {e}")
        return 2048  # Default fallback

def safe_write_message(messages_file, message):
    """Safely write a message to the file with error handling"""
    try:
        with open(messages_file, 'a', encoding='utf-8') as file:
            file.write(json.dumps(message, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Error writing message to file: {e}")
        raise

def safe_read_messages(messages_file):
    """Safely read messages from file with error handling"""
    try:
        with open(messages_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            messages = []
            for line in lines:
                if line.strip():
                    try:
                        message = json.loads(line.strip())
                        if isinstance(message, dict) and 'role' in message and 'content' in message:
                            messages.append(message)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON line: {e}")
                        continue
            return messages
    except FileNotFoundError:
        logger.info("Messages file not found, starting fresh conversation")
        return []
    except Exception as e:
        logger.error(f"Error reading messages file: {e}")
        return []

def runData(text, model):
    try:
        # Validate inputs
        text = validate_input(text)
        model = validate_model_name(model)
        
        messages_file = get_messages_file_path()
        
        # Append user message
        safe_write_message(messages_file, {"role": "user", "content": text})

        # Read existing messages
        theMessages = safe_read_messages(messages_file)

        num_ctx = get_dynamic_num_ctx(theMessages)

        # Send messages to Ollama
        stream = ollama.chat(model=model, messages=theMessages, stream=True, options={"num_ctx": num_ctx})

        full_response = ""

        for chunk in stream:
            word = chunk.get('message', {}).get('content', '')
            full_response += word
            yield word  # yield word-by-word

        # Append assistant response
        safe_write_message(messages_file, {"role": "assistant", "content": full_response})
        
    except Exception as e:
        logger.error(f"Error in runData: {e}")
        yield f"Error: {str(e)}"

def runImage(text, imagePath):
    try:
        # Validate inputs
        text = validate_input(text)
        
        if not os.path.exists(imagePath):
            yield "Error: The provided image path does not exist."
            return
        
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
        safe_write_message(messages_file, {"role": "assistant", "content": full_response})
        
    except Exception as e:
        logger.error(f"Error in runImage: {e}")
        yield f"Error: {str(e)}"

