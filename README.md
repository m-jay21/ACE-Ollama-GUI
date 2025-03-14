# **ACE (Ollama GUI for Windows)**

## **Overview**
**ACE** is a graphical user interface (GUI) for **Ollama**, designed to eliminate the need for command-line usage. This project provides an intuitive interface for users to interact with locally installed AI models.

## **Features**
- **PDF Processing**: Upload and analyze PDFs.
- **Image Processing**: Upload and analyze images.
- **Model Selection**: Easily switch between installed AI models.
- **Install New Models**: Install compatible Ollama models directly from the UI.
- **Session Memory**: Remembers context within a session for a continuous conversation.
- **Local Execution**: Run models directly on your machine without an internet connection.
- **Real-time Output**: Word-by-word rendering for a natural, real-time effect.

## **Planned Features**
- **Prompt Modes**: Predefined modes (e.g., “Explain like I’m five”) for different use cases.
- **Model Management**: Ability to remove and delete installed models.
- **Encryption Tool**: Secure message history using AES-256 encryption with a user-provided password.

---

## **Installation**

### **Requirements**
- **Python**: Version **3.8** or later
- **Ollama**: Must be installed and running.

### **Install Dependencies**
Run the following command:

```sh
pip install ollama pymupdf customtkinter pillow tiktoken
```

### **Additional Dependencies**
- **tkinter** (Pre-installed with Python but ensure availability)
- **threading** and **time** (Standard Python libraries)

### **External Files Required**
- **Theme File:** `theme.json` (For UI styling)
- **Icons/Images:**  
  - `logo2.ico` (Application icon)  
  - `up-loading.ico` (Upload button icon)  
  - `logo2.png` (Displayed in the UI)
- **Message Storage:** `theMessages.txt` (Stores conversation history)

### **Ollama Models**
- Users must have **Ollama installed and running**.
- Install at least **one AI model** compatible with Ollama.
- The **"llava:latest"** model is required for image processing.

### **Operating System Compatibility**
- Works on **Windows, macOS, and Linux** (as long as Python and required dependencies are installed).

---

## **Setup & Running the Application**
### **1. Clone the repository**
```sh
git clone https://github.com/m-jay21/ACE-Ollama-GUI.git
cd ACE-Ollama-GUI
```

### **2. Create a Virtual Environment (Recommended)**
```sh
python -m venv env
source env/bin/activate   # On macOS/Linux
env\Scripts\activate      # On Windows
```

### **3. Install Dependencies**
```sh
pip install -r requirements.txt
```

### **4. Start Ollama (if not running)**
```sh
ollama serve
```

### **5. Run the GUI**
```sh
python ui.py
```

---

## **Usage**
1. **Launch ACE** by running `python ui.py`.
2. **Select an installed AI model** or install a new one from the **Settings** tab.
3. **Upload PDFs or images** for processing.
4. **Enter prompts** and receive real-time responses.

---

## **Screenshots**
![Screenshot](images/image1.png)  
![Screenshot](images/image2.png)  
![Screenshot](images/image3.png)  

---

## **Contributing**
Contributions are welcome! To contribute:

1. **Fork** the repository.
2. **Create a new branch** for your feature/fix.
3. **Commit and push** your changes.
4. **Submit a pull request**.

---

## **Issues & Support**
If you encounter any issues, feel free to open an issue on GitHub.

---

## **License**
This project is licensed under the **MIT License**.

---

## **Need Help?**
Reach out via **GitHub Discussions**.
