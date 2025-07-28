# **ACE (Ollama GUI for Windows)**

## **Overview**
**ACE** is a graphical user interface (GUI) for **Ollama**, designed to eliminate the need for command-line usage. This project provides an intuitive interface for users to interact with locally installed AI models. Built as an Electron application for better cross-platform compatibility and user experience.

## **Features**
- **Modern UI**: Clean, responsive interface with customizable themes
- **Enhanced PDF Processing**: Upload and analyze PDFs with intelligent document chunking and preprocessing
- **Document Chunking**: Advanced text preprocessing and intelligent document splitting for better AI responses
- **RAG Pipeline**: Retrieval-Augmented Generation foundation for context-aware AI interactions
- **Image Processing**: Upload and analyze images with improved preview
- **Model Selection**: Intuitive model selection with real-time status indicators
- **Install New Models**: One-click installation of compatible Ollama models
- **Session Memory**: Advanced context management for continuous conversations
- **Clear Chat**: Allows for the user to clear the chat's memory to start anew
- **Local Execution**: Run models directly on your machine without internet dependency
- **Real-time Output**: Smooth, word-by-word rendering for natural conversation flow
- **Theme Customization**: Choose from multiple themes to personalize your experience
- **Windows Native**: Optimized for Windows with native installer support

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
pip install -r requirements.txt

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

### **Verification**
The SHA256 hash for the latest release can be verified using:
```
DFA9935EFE93010F92BA76CC6037BC41852A2F9D6DC4E08D2155BF59B47BE88E
```

---

## **Usage**
1. **Launch ACE**
2. **Select an installed AI model** or install a new one from the **Settings** tab
3. **Upload PDFs or images** for processing (PDFs use enhanced chunking automatically)
4. **Enter prompts** and receive real-time responses with context-aware AI interactions
5. Use the **Clear Chat** button to start a new conversation

### **Enhanced PDF Processing**
ACE now features intelligent document chunking and preprocessing:
- **Document Chunking**: PDFs are automatically split into meaningful chunks
- **Text Preprocessing**: Clean and normalize text for better AI understanding
- **Context-Aware Responses**: AI receives relevant document sections instead of entire text
- **RAG Pipeline**: Foundation for retrieval-augmented generation

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
