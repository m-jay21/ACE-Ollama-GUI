import threading
import customtkinter as ctk
from PIL import Image
from queue import Queue
import aiTool

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


output_queue = Queue()

def update_ui_from_queue():
    #removes test from the queue and puts it into the response box
    while not output_queue.empty():
        text_fragment = output_queue.get()
        response_textbox.configure(state="normal")
        response_textbox.insert("end", text_fragment)
        response_textbox.configure(state="disabled")
        response_textbox.yview_moveto(1.0)
        response_textbox.update_idletasks() 
    app.after(100, update_ui_from_queue)

#updates the ui every so often
app.after(100, update_ui_from_queue)

#callback functions
def on_word_callback(text_fragment):
    print(f"Debug: Adding to queue -> {repr(text_fragment)}")
    #pushes text into queue
    output_queue.put(text_fragment)

def on_done_callback():
    #turns on the textbox and enter button when the ai is done
    app.after(0, lambda: (
        textbox.configure(state="normal"),
        enter_button.configure(state="normal")
    ))

#ai submission handling
def aiSubmission(text):
    model = option_menu.get()
    #turns off the textbox and enter button
    textbox.configure(state="disabled")
    enter_button.configure(state="disabled")
    
    #clears the preivous entry in the response box
    response_textbox.configure(state="normal")
    response_textbox.delete("1.0", "end")
    response_textbox.configure(state="disabled")
    
    #lauches the ai tool
    threading.Thread(
        target=aiTool.runData, 
        args=(text, model, on_word_callback, on_done_callback), 
        daemon=True
    ).start()

def commandSubmission(text):
    #clears the preivous entry in the response box
    response_textbox.configure(state="normal")
    response_textbox.delete("1.0", "end")
    response_textbox.configure(state="disabled")

    threading.Thread(
        target=aiTool.runCommand, 
        args=(text, on_word_callback, on_done_callback), 
        daemon=True
    ).start()

#keybindings
def toggleFullscreen(event=None):
    current = app.attributes("-fullscreen")
    app.attributes("-fullscreen", not current)

def escapeFullscreen(event=None):
    app.attributes("-fullscreen", False)

def enterText(event=None):
    text = textbox.get("1.0", "end").strip()
    textbox.delete("1.0", "end")
    if text and commandMode.get() == False:
        aiSubmission(text)
    elif text and commandMode.get() == True:
        commandSubmission(text)

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
app.grid_rowconfigure(0, weight=0)   #top logo
app.grid_rowconfigure(1, weight=3)   #response box area
app.grid_rowconfigure(2, weight=1)   #input area
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=0)

#logo box
top_box = ctk.CTkFrame(app, border_width=2)
top_box.grid(row=0, column=0, columnspan=2, sticky="nsew")
try:
    logo_image = ctk.CTkImage(light_image=Image.open("logo2.png"), size=(100, 100))
    image_label = ctk.CTkLabel(top_box, image=logo_image, text="")
    image_label.place(relx=0.5, rely=0.5, anchor="center")
except Exception as e:
    print("Logo load error:", e)

#response box area
response_textbox = ctk.CTkTextbox(app, wrap="word", state="disabled", border_width=0, padx=20)
response_textbox.configure(fg_color="#121b26")
response_textbox.configure(corner_radius=0)
response_textbox.grid(row=1, column=0, columnspan=2, sticky="nsew")

#textbox area
textbox = ctk.CTkTextbox(app, border_width=2, padx=10, pady=10)
textbox.grid(row=2, column=0, sticky="nsew")

bottom_left_box = ctk.CTkFrame(app, border_width=2)
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

bottom_section = ctk.CTkFrame(bottom_left_box, border_width=2)
bottom_section.grid(row=2, column=0, sticky="nsew")
commandMode = ctk.BooleanVar()
checkbox = ctk.CTkCheckBox(bottom_section, text="Command Mode", variable=commandMode, font=bold_font)
checkbox.grid(row=0, column=0, padx=10, pady=10, sticky="w")

#start the app
app.mainloop()
