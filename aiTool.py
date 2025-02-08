import subprocess
import re
import time
import sys
import msvcrt

def aiOptions():
    #retrieves all the models already installed
    command = "ollama list"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    lines = result.stdout.strip().split("\n")
    #give only the model names and skip the headers, etc
    return [line.split()[0] for line in lines[1:]] if len(lines) > 1 else []

def cleanAnsi(text):
    #removes any ansi characters and spinning values that ollama outputs
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    spinner_artifacts = re.compile(r'[⠋⠙⠹⠼⠧⠇⠏⠸⠴⠦⠬⠰⠾⠶⠖⠆⠖⠲]+')
    text = ansi_escape.sub('', text)
    text = spinner_artifacts.sub('', text)
    #keeps a space after punctuation if needed.
    text = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', text)
    return text

def runCommand(text, word_callback, done_callback):
    try:
        process = subprocess.Popen(
            text,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=0
        )

        #send the input text and close stdin
        process.stdin.write(text + "\n")
        process.stdin.flush()
        process.stdin.close()

        word_buffer = ""

        while True:
            char = process.stdout.read(1)  #read one character at a time

            if not char:
                time.sleep(2)
                if process.poll() is not None:  #process has finished
                    break
                time.sleep(2)  #avoid busy-waiting if no output is available
                continue

            cleaned_char = cleanAnsi(char)

            if cleaned_char in " \n":  #a word has completed
                if word_buffer:
                    word_callback(word_buffer + cleaned_char)
                    word_buffer = ""
                else:
                    word_callback(cleaned_char)
            else:
                word_buffer += cleaned_char  #build up the word


                sys.stdout.flush()  #ensure immediate display

            if process.poll() is not None and not word_buffer:
                break  #stop when process is fully done

        if word_buffer:
            word_callback(word_buffer)  #send any remaining word

        done_callback()
        
    except FileNotFoundError:
        word_callback("⚠️ Error: Ollama is not installed or not in PATH.")
        done_callback()
    except Exception as e:
        word_callback(f"⚠️ Unexpected error: {e}")
        done_callback()


def runData(text, model, word_callback, done_callback):
    try:
        process = subprocess.Popen(
            ["ollama", "run", model],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=0
        )

        #send the input text and close stdin
        process.stdin.write(text + "\n")
        process.stdin.flush()
        process.stdin.close()

        word_buffer = ""

        while True:
            char = process.stdout.read(1)  #read one character at a time

            if not char:
                time.sleep(2)
                if process.poll() is not None:  #process has finished
                    break
                time.sleep(2)  #avoid busy-waiting if no output is available
                continue

            cleaned_char = cleanAnsi(char)

            if cleaned_char in " \n":  #a word has completed
                if word_buffer:
                    word_callback(word_buffer + cleaned_char)
                    word_buffer = ""
                else:
                    word_callback(cleaned_char)
            else:
                word_buffer += cleaned_char  #build up the word


                sys.stdout.flush()  #ensure immediate display

            if process.poll() is not None and not word_buffer:
                break  #stop when process is fully done

        if word_buffer:
            word_callback(word_buffer)  #send any remaining word

        done_callback()

    except FileNotFoundError:
        word_callback("⚠️ Error: Ollama is not installed or not in PATH.")
        done_callback()
    except Exception as e:
        word_callback(f"⚠️ Unexpected error: {e}")
        done_callback()