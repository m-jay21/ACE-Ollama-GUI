import threading
import customtkinter as ctk
from PIL import Image
from queue import Queue
import aiTool
import time

#application and ui setup
app = ctk.CTk()
app.title("ACE AI")

#fonts
normal_font = ctk.CTkFont(family="Arial", size=14)
bold_font = ctk.CTkFont(family="Arial", size=14, weight="bold")

#window settings
app.geometry("800x625")
app.resizable(True, True)
try:
    app.iconbitmap("logo2.ico")
except Exception as e:
    print("Icon load error:", e)
ctk.set_default_color_theme("theme.json")
ctk.set_appearance_mode("Dark")

output_queue = Queue()

def update_response(word):
    response_textbox.configure(state="normal")
    response_textbox.insert("end", word)
    response_textbox.configure(state="disabled")
    response_textbox.yview_moveto(1.0)

def reactivate():
    #turns on the textbox and enter button when the AI is done
    def enable_inputs():
        textbox.configure(state="normal")
        enter_button.configure(state="normal")
    
    app.after(0, enable_inputs)

#ai submission handling
def aiSubmission(text):
    model = option_menu.get()
    textbox.configure(state="disabled")
    enter_button.configure(state="disabled")

    #tags for textbox
    response_textbox.tag_config("right", justify="right")
    response_textbox.tag_config("left", justify="left")
    
    #shows users response
    response_textbox.configure(state="normal")
    response_textbox.insert("end", "\n")
    response_textbox.insert("end", "\n")
    response_textbox.insert("end", "\n")
    response_textbox.insert("end", text, ("right")) 
    response_textbox.insert("end", "\n")
    response_textbox.insert("end", "\n")
    response_textbox.insert("end", "\n")
    response_textbox.configure(state="disabled")

    def run_ai():
        for word in aiTool.runData(text, model):
            app.after(0, lambda: update_response(word))  
            time.sleep(0.05)
        app.after(0, reactivate)

    threading.Thread(target=run_ai, daemon=True).start()

#keybindings
def toggleFullscreen(event=None):
    current = app.attributes("-fullscreen")
    app.attributes("-fullscreen", not current)

def escapeFullscreen(event=None):
    app.attributes("-fullscreen", False)

responseDown = ""

def enterDownload(event=None):
    text = modelDown.get().strip()
    modelDown.delete(0, "end") 
    if text:
        responseDown = aiTool.downloadModel(text)

    download_button.configure(state="disabled")
    downloadedResponse.configure(state="normal")
    downloadedResponse.delete("1.0", "end")
    downloadedResponse.insert("end", responseDown)
    downloadedResponse.configure(state="disabled")
    download_button.configure(state="normal")

def enterText(event=None):
    response_textbox.yview_moveto(1.0)
    text = textbox.get("1.0", "end").strip()
    textbox.delete("1.0", "end")
    if text:
        aiSubmission(text)

def newLine(event=None):
    textbox.insert("insert", "\n")
    return "break"

def select_previous_word(event):
    pos = response_textbox.index("insert") 
    before_text = response_textbox.get("1.0", pos) 

    if before_text.strip():  
        words = before_text.split()
        if words:
            last_word = words[-1]  # Get the last word
            start_index = f"{pos} - {len(last_word)}c"  # Move selection back
            response_textbox.tag_remove("sel", "1.0", "end")  # Clear selection
            response_textbox.tag_add("sel", start_index, pos)  # Select the word
            response_textbox.mark_set("insert", start_index)  # Move cursor

    return "break"  

def select_next_word(event):
    pos = response_textbox.index("insert")  # Get current cursor position
    after_text = response_textbox.get(pos, "end")  # Text after cursor

    if after_text.strip():  # Ensure there's text after cursor
        words = after_text.split()
        if words:
            next_word = words[0]  # Get the first word after cursor
            end_index = f"{pos} + {len(next_word)}c"  # Move selection forward
            response_textbox.tag_remove("sel", "1.0", "end")  # Clear selection
            response_textbox.tag_add("sel", pos, end_index)  # Select the word
            response_textbox.mark_set("insert", end_index)  # Move cursor

    return "break"  # Prevent default behavior

app.bind("<F11>", toggleFullscreen)
app.bind("<Escape>", escapeFullscreen)
app.bind("<Return>", enterText)
app.bind("<Shift-Return>", newLine)
app.bind("<Control-Shift-Left>", select_previous_word)
app.bind("<Control-Shift-Right>", select_next_word)

#configure grid rows and columns.
tabview = ctk.CTkTabview(app)
tabview.pack(expand=True, fill="both", padx=20, pady=20)
tabview.configure(fg_color="#121b26")

#main tab
aiTab = tabview.add("Main Tab")

aiTab.grid_rowconfigure(0, weight=0)   #top logo
aiTab.grid_rowconfigure(1, weight=3)   #response box area
aiTab.grid_rowconfigure(2, weight=1)   #input area
aiTab.grid_columnconfigure(0, weight=1)
aiTab.grid_columnconfigure(1, weight=0)

#logo box
top_box = ctk.CTkFrame(aiTab, border_width=2)
top_box.grid(row=0, column=0, columnspan=2, sticky="nsew")
try:
    logo_image = ctk.CTkImage(light_image=Image.open("logo2.png"), size=(100, 100))
    image_label = ctk.CTkLabel(top_box, image=logo_image, text="")
    image_label.place(relx=0.5, rely=0.5, anchor="center")
except Exception as e:
    print("Logo load error:", e)

#response box area
response_textbox = ctk.CTkTextbox(aiTab, wrap="word", state="disabled", border_width=0, padx=20)
response_textbox.configure(fg_color="#121b26")
response_textbox.configure(corner_radius=0)
response_textbox.grid(row=1, column=0, columnspan=2, sticky="nsew")

#textbox area
textbox = ctk.CTkTextbox(aiTab, border_width=2, padx=10, pady=10)
textbox.grid(row=2, column=0, sticky="nsew")

bottom_left_box = ctk.CTkFrame(aiTab, border_width=2)
bottom_left_box.grid(row=2, column=1, sticky="nsew")

#enter button and ai options
top_section = ctk.CTkFrame(bottom_left_box, border_width=2)
top_section.grid(row=0, column=0, sticky="nsew")
enter_button = ctk.CTkButton(top_section, text="Enter", font=bold_font, command=enterText)
enter_button.grid(row=0, column=0, padx=10, pady=10)

#pull the ai options
aiOptions = aiTool.aiOptions()
middle_section = ctk.CTkFrame(bottom_left_box, border_width=2)
middle_section.grid(row=1, column=0, sticky="nsew")
option_menu = ctk.CTkOptionMenu(middle_section, values=aiOptions)
option_menu.grid(row=0, column=0, padx=10, pady=10)


#setting the background colors
app.configure(fg_color="#121b26")

tabview.configure(fg_color="#121b26")

#set individual frame backgrounds
top_box.configure(fg_color="#121b26")
bottom_left_box.configure(fg_color="#121b26")

#settings tab
settingsTab = tabview.add("Settings")

#columns formation
settingsTab.grid_columnconfigure(0, weight=1)
settingsTab.grid_columnconfigure(1, weight=1)

#message explaining everything
messageD = ctk.CTkLabel(settingsTab, text="Download any model compatible with Ollama:", font=bold_font)
messageD.grid(row=0, column=0, columnspan=2, pady=10)

#frame for the textbox and button
entry_button_frame = ctk.CTkFrame(settingsTab)
entry_button_frame.grid(row=1, column=0, columnspan=2, pady=10)

#text box to enter model name
modelDown = ctk.CTkEntry(entry_button_frame, placeholder_text="Model Name")
modelDown.grid(row=1, column=0, padx=(0, 10)) 

#download button
download_button = ctk.CTkButton(entry_button_frame, text="Download", font=bold_font, command=enterDownload)
download_button.grid(row=1, column=1)

#response after downloading
downloadedResponse = ctk.CTkTextbox(entry_button_frame, state="disabled", border_width=0, font=bold_font)
downloadedResponse.grid(row=2, column=0, columnspan=2, pady=10)
downloadedResponse.configure(fg_color="#121b26")

#start the app
app.mainloop()

#empty out text file
with open("theMessages.txt", "w") as file:
    file.write("")

