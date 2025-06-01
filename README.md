# **ACE (Ollama GUI for Windows)**

## **Overview**
**ACE** is a graphical user interface (GUI) for **Ollama**, designed to eliminate the need for command-line usage. This project provides an intuitive interface for users to interact with locally installed AI models. Built as an Electron application for better cross-platform compatibility and user experience.

## **Features**
- **PDF Processing**: Upload and analyze PDFs.
- **Image Processing**: Upload and analyze images.
- **Model Selection**: Easily switch between installed AI models.
- **Install New Models**: Install compatible Ollama models directly from the UI.
- **Session Memory**: Remembers context within a session for a continuous conversation.
- **Local Execution**: Run models directly on your machine without an internet connection.
- **Real-time Output**: Word-by-word rendering for a natural, real-time effect.
- **Cross-platform**: Works on Windows, macOS, and Linux.

## **Planned Features**
- **Prompt Modes**: Predefined modes (e.g., "Explain like I'm five") for different use cases.
- **Model Management**: Ability to remove and delete installed models.
- **Encryption Tool**: Secure message history using AES-256 encryption with a user-provided password.

---

## **Installation**

### **Requirements**
- **Python**: Version **3.8** or later
- **Ollama**: Must be installed and running
- **Node.js**: Version **14** or later (for development only)

### **For Users**
1. Download the latest release from the [Releases](https://github.com/m-jay21/ACE-Ollama-GUI/releases) page
2. Install the application
3. Make sure Ollama is installed and running
4. Launch ACE and start using it!

### **For Developers**

#### **1. Clone the repository**
```sh
git clone https://github.com/m-jay21/ACE-Ollama-GUI.git
cd ACE-Ollama-GUI
```

#### **2. Install Dependencies**
```sh
# Install Python dependencies
pip install ollama pymupdf pillow tiktoken

# Install Node.js dependencies
npm install
```

#### **3. Start Ollama (if not running)**
```sh
ollama serve
```

#### **4. Run the Application**
```sh
# For development
npm start

# To build the application
npm run dist
```

---

## **Usage**
1. **Launch ACE**
2. **Select an installed AI model** or install a new one from the **Settings** tab
3. **Upload PDFs or images** for processing
4. **Enter prompts** and receive real-time responses
5. Use the **Clear Chat** button to start a new conversation

---

## **Development**
The application is built using:
- **Electron**: For the desktop application framework
- **Python**: For AI model interaction and processing
- **HTML/CSS/JavaScript**: For the user interface

### **Project Structure**
- `main.js`: Main Electron process
- `index.html`: Main application window
- `*.py`: Python scripts for AI processing
- `package.json`: Node.js dependencies and build configuration

---

## **Contributing**
Contributions are welcome! To contribute:

1. **Fork** the repository
2. **Create a new branch** for your feature/fix
3. **Commit and push** your changes
4. **Submit a pull request**

---

## **Issues & Support**
If you encounter any issues:
1. Check if Ollama is running
2. Ensure you have the required Python version
3. Open an issue on GitHub with:
   - Your operating system
   - Python version
   - Ollama version
   - Steps to reproduce the issue

---

## **License**
This project is licensed under the **MIT License**.

---

## **Need Help?**
Reach out via **GitHub Discussions** or open an issue.
