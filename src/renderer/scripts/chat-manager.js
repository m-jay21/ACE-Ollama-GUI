class ChatManager {
  constructor(uiManager, ipcHandlers) {
    this.uiManager = uiManager;
    this.ipcHandlers = ipcHandlers;
    this.selectedFilePath = "";
    this.isProcessing = false;
    this.init();
  }

  init() {
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    // Submit button click
    this.uiManager.submitButton.addEventListener('click', () => {
      this.handleSubmit();
    });

    // File upload handling
    this.uiManager.uploadButton.addEventListener('click', async () => {
      await this.handleFileUpload();
    });

    // Clear chat handling
    this.uiManager.clearChatButton.addEventListener('click', async () => {
      await this.handleClearChat();
    });

    // Model download handling
    this.uiManager.downloadButton.addEventListener('click', async () => {
      await this.handleModelDownload();
    });
  }

  async handleSubmit() {
    if (this.isProcessing) {
      return; // Prevent multiple simultaneous requests
    }

    const query = this.uiManager.queryInput.value.trim();
    const model = this.uiManager.modelSelect.value;
    
    if (query === "") {
      this.showUserFeedback("Please enter a message", "warning");
      return;
    }

    if (!model || model === "No models found") {
      this.showUserFeedback("Please select a valid AI model", "error");
      return;
    }

    this.isProcessing = true;

    // Hide empty state and show loading
    this.uiManager.hideEmptyState();
    this.uiManager.setUserInputEnabled(false);
    this.uiManager.showSpinner();

    // Add user message to chat
    this.addUserMessage(query);

    // Reset input
    this.uiManager.resetQueryInput();

    try {
      // Send query to AI
      await this.ipcHandlers.submitAIQuery(query, model, this.selectedFilePath);
    } catch (error) {
      console.error("Error in AI query:", error);
      
      let errorMessage = "Error processing your request. Please try again.";
      
      // Provide more specific error messages
      if (error.message.includes("timeout")) {
        errorMessage = "Request timed out. The AI model is taking too long to respond.";
      } else if (error.message.includes("Python process")) {
        errorMessage = "Failed to start AI processing. Please check if Python and Ollama are properly installed.";
      } else if (error.message.includes("Invalid model name")) {
        errorMessage = "Invalid model selected. Please choose a different model.";
      } else if (error.message.includes("File")) {
        errorMessage = "Error processing the uploaded file. Please try a different file.";
      }
      
      this.addErrorMessage(errorMessage);
    } finally {
      // Re-enable input and hide spinner
      this.uiManager.setUserInputEnabled(true);
      this.uiManager.hideSpinner();
      this.selectedFilePath = "";
      this.isProcessing = false;
    }
  }

  async handleFileUpload() {
    try {
      const filePath = await this.ipcHandlers.openFileDialog();
      if (filePath) {
        this.selectedFilePath = filePath;
        console.log("Selected file: " + this.selectedFilePath);
        
        // Show user feedback about selected file
        const fileName = filePath.split(/[\\/]/).pop(); // Get filename from path
        this.showUserFeedback(`File selected: ${fileName}`, "success");
      }
    } catch (error) {
      console.error("Error in file upload:", error);
      this.showUserFeedback("Error selecting file. Please try again.", "error");
    }
  }

  async handleClearChat() {
    try {
      // Ensure valid model is selected
      if (!this.uiManager.modelSelect.value || this.uiManager.modelSelect.value === "No models found") {
        const options = await this.ipcHandlers.getAIOptions();
        this.uiManager.populateModelSelect(options);
        
        if (!this.uiManager.modelSelect.value || this.uiManager.modelSelect.value === "No models found") {
          this.showUserFeedback("No valid model available. Please install a model first.", "error");
          return;
        }
      }

      // Clear chat through IPC
      await this.ipcHandlers.clearChat();
      
      // Clear UI
      this.uiManager.clearChatWindow();
      this.showUserFeedback("Chat cleared successfully", "success");
    } catch (error) {
      console.error('Error clearing chat:', error);
      this.showUserFeedback("Error clearing chat. Please try again.", "error");
    }
  }

  async handleModelDownload() {
    const modelName = this.uiManager.modelDownloadInput.value.trim();
    if (modelName === "") {
      this.showUserFeedback("Please enter a model name", "warning");
      return;
    }
    
    // Show progress and disable button
    this.uiManager.downloadProgress.classList.remove('hidden');
    this.uiManager.downloadResponse.classList.add('hidden');
    this.uiManager.downloadButton.disabled = true;
    this.uiManager.downloadButton.textContent = "Downloading...";
    
    // Reset progress
    this.uiManager.progressBar.style.width = "0%";
    this.uiManager.progressText.textContent = "Starting download...";
    this.uiManager.progressPercentage.textContent = "0%";
    
    try {
      const result = await this.ipcHandlers.downloadModel(modelName);

      let parsedResult = result;
      if (typeof result === 'string') {
        try {
          parsedResult = JSON.parse(result);
        } catch (e) {
          parsedResult = { status: result, progress: 100 };
        }
      }

      // Handle download result
      if (parsedResult.status === "Cannot be installed" || parsedResult.stage === "error") {
        this.showDownloadError("Failed to install model. Please check if the model name is correct and try again.");
      } else if (parsedResult.status === "Model installed successfully!" || parsedResult.stage === "complete" || parsedResult.progress === 100) {
        this.showDownloadSuccess();
        
        // Refresh model list after successful download
        try {
          const options = await this.ipcHandlers.getAIOptions();
          this.uiManager.populateModelSelect(options);
        } catch (error) {
          console.error("Error refreshing model list:", error);
        }
      }
    } catch (error) {
      console.error("Download error:", error);
      this.showDownloadError(`Error: ${error.message}`);
    }
  }

  showDownloadError(message) {
    this.uiManager.progressBar.style.width = "0%";
    this.uiManager.progressText.textContent = "Download failed";
    this.uiManager.progressPercentage.textContent = "";
    this.uiManager.downloadResponse.textContent = message;
    this.uiManager.downloadResponse.classList.remove('hidden');
    this.uiManager.downloadProgress.classList.add('hidden');
    this.uiManager.downloadButton.disabled = false;
    this.uiManager.downloadButton.textContent = "Download";
  }

  showDownloadSuccess() {
    this.uiManager.progressBar.style.width = "100%";
    this.uiManager.progressText.textContent = "Model installed successfully!";
    this.uiManager.progressPercentage.textContent = "100%";
    this.uiManager.downloadResponse.textContent = "Model installed successfully!";
    this.uiManager.downloadResponse.classList.remove('hidden');
    this.uiManager.downloadProgress.classList.add('hidden');
    this.uiManager.downloadButton.disabled = false;
    this.uiManager.downloadButton.textContent = "Download";
  }

  showUserFeedback(message, type = "info") {
    // Create a temporary feedback element
    const feedback = document.createElement('div');
    feedback.className = `fixed top-4 left-1/2 transform -translate-x-1/2 z-50 px-4 py-2 rounded-lg text-white text-sm transition-all duration-300 ${
      type === 'error' ? 'bg-red-500' :
      type === 'success' ? 'bg-green-500' :
      type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
    }`;
    feedback.textContent = message;
    
    document.body.appendChild(feedback);
    
    // Remove after 3 seconds
    setTimeout(() => {
      if (feedback.parentNode) {
        feedback.parentNode.removeChild(feedback);
      }
    }, 3000);
  }

  addUserMessage(text) {
    const userMessage = document.createElement('div');
    userMessage.className = 'flex justify-end mb-4';
    
    const userMessageContent = document.createElement('div');
    userMessageContent.className = 'bg-[var(--accent)] text-[var(--bg-primary)] p-3 rounded-lg whitespace-pre-wrap break-words max-w-[80%]';
    userMessageContent.textContent = text;
    
    userMessage.appendChild(userMessageContent);
    this.uiManager.chatWindow.appendChild(userMessage);
    this.uiManager.autoScroll();
  }

  addErrorMessage(text) {
    const errorMessage = document.createElement('div');
    errorMessage.className = 'flex justify-start mb-4';
    
    const errorMessageContent = document.createElement('div');
    errorMessageContent.className = 'bg-red-500 text-white p-3 rounded-lg whitespace-pre-wrap break-words max-w-[80%]';
    errorMessageContent.textContent = text;
    
    errorMessage.appendChild(errorMessageContent);
    this.uiManager.chatWindow.appendChild(errorMessage);
    this.uiManager.autoScroll();
  }

  handleAIStream(data) {
    const lastChild = this.uiManager.chatWindow.lastElementChild;
    
    if (lastChild && lastChild.classList.contains('ai-message')) {
      // Append to existing AI message
      lastChild.querySelector('.message-content').textContent += data;
    } else {
      // Create new AI message
      const aiMessage = document.createElement('div');
      aiMessage.className = 'flex justify-start mb-4 ai-message';
      
      const aiMessageContent = document.createElement('div');
      aiMessageContent.className = 'bg-[var(--bg-tertiary)] text-[var(--text-primary)] p-3 rounded-lg whitespace-pre-wrap break-words max-w-[80%] message-content';
      aiMessageContent.textContent = data;
      
      aiMessage.appendChild(aiMessageContent);
      this.uiManager.chatWindow.appendChild(aiMessage);
    }
    
    this.uiManager.autoScroll();
  }
}

// Export for use in other modules
window.ChatManager = ChatManager; 