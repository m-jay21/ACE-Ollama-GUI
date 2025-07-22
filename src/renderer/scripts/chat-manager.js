class ChatManager {
  constructor(uiManager, ipcHandlers) {
    this.uiManager = uiManager;
    this.ipcHandlers = ipcHandlers;
    this.selectedFilePath = "";
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
    const query = this.uiManager.queryInput.value.trim();
    const model = this.uiManager.modelSelect.value;
    
    if (query === "") return;

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
      this.addErrorMessage("Error processing your request. Please try again.");
    } finally {
      // Re-enable input and hide spinner
      this.uiManager.setUserInputEnabled(true);
      this.uiManager.hideSpinner();
      this.selectedFilePath = "";
    }
  }

  async handleFileUpload() {
    const filePath = await this.ipcHandlers.openFileDialog();
    if (filePath) {
      this.selectedFilePath = filePath;
      console.log("Selected file: " + this.selectedFilePath);
      // You could add UI feedback here to show file is selected
    }
  }

  async handleClearChat() {
    try {
      // Ensure valid model is selected
      if (!this.uiManager.modelSelect.value || this.uiManager.modelSelect.value === "No models found") {
        const options = await this.ipcHandlers.getAIOptions();
        this.uiManager.populateModelSelect(options);
        
        if (!this.uiManager.modelSelect.value || this.uiManager.modelSelect.value === "No models found") {
          console.error('No valid model available');
          return;
        }
      }

      // Clear chat through IPC
      await this.ipcHandlers.clearChat();
      
      // Clear UI
      this.uiManager.clearChatWindow();
    } catch (error) {
      console.error('Error clearing chat:', error);
    }
  }

  async handleModelDownload() {
    const modelName = this.uiManager.modelDownloadInput.value.trim();
    if (modelName === "") return;
    
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
      if (parsedResult.status === "Cannot be installed") {
        this.showDownloadError("Failed to install model. Please check if the model name is correct and try again.");
      } else if (parsedResult.status === "Installed" || parsedResult.progress === 100) {
        this.showDownloadSuccess();
      }
    } catch (error) {
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