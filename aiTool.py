import re
import ollama
import json
import tiktoken

def aiOptions():
    response = ollama.list()

    model_names = [model.model for model in response.models]
    return(model_names)

def cleanAnsi(text):
    #removes any ansi characters and spinning values that ollama outputs
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    spinner_artifacts = re.compile(r'[⠋⠙⠹⠼⠧⠇⠏⠸⠴⠦⠬⠰⠾⠶⠖⠆⠖⠲]+')
    text = ansi_escape.sub('', text)
    text = spinner_artifacts.sub('', text)
    #keeps a space after punctuation if needed.
    text = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', text)
    return text

def downloadModel(text):
    if text in aiOptions():
        return "Already Installed"
    try:
        ollama.pull(text)
    except Exception as e:
        return "Cannot be installed"
    
    return "Installed"

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
    #append user message
    with open("theMessages.txt", 'a') as file:
        file.write(json.dumps({"role": "user", "content": text}) + "\n")

    #open the file for reading
    with open("theMessages.txt", 'r') as file:
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
    with open("theMessages.txt", 'a') as file:
        file.write(json.dumps({"role": "assistant", "content": full_response}) + "\n")