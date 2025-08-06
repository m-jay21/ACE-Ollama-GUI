class ChatManager {
  constructor(uiManager, ipcHandlers) {
    this.uiManager = uiManager;
    this.ipcHandlers = ipcHandlers;
    this.selectedFilePath = "";
    this.isProcessing = false;
    this.observabilitySettings = {
      showTokens: true,
      showSources: true,
      showDetails: false
    };
    this.init();
  }

  init() {
    this.setupEventHandlers();
    this.loadObservabilitySettings();
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
    
    // Observability settings handling
    this.setupObservabilityHandlers();
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
      // Don't clear loading state here - let the completion signal handle it
      
      // Fallback: if completion signal doesn't arrive within 3 seconds, clear loading state
      setTimeout(() => {
        if (this.isProcessing) {
          this.clearLoadingState();
        }
      }, 3000);
      
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
      
      // Clear loading state on error
      this.clearLoadingState();
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
        const fileExt = fileName.split('.').pop().toLowerCase();
        
        // Document types that support semantic search
        const documentTypes = ['pdf', 'txt', 'md', 'csv', 'json', 'docx', 'doc'];
        const imageTypes = ['png', 'jpg', 'jpeg', 'bmp', 'gif'];
        
        if (documentTypes.includes(fileExt)) {
          this.showUserFeedback(`Document selected: ${fileName} (Semantic search enabled)`, "success");
        } else if (imageTypes.includes(fileExt)) {
          this.showUserFeedback(`Image selected: ${fileName}`, "success");
        } else {
        this.showUserFeedback(`File selected: ${fileName}`, "success");
        }
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
    
    // Reset progress for enhanced interface
    this.uiManager.progressBar.style.width = "0%";
    this.uiManager.progressPercentage.textContent = "0%";
    this.uiManager.downloadStage.textContent = "Initializing...";
    this.uiManager.downloadSpeed.textContent = "-";
    this.uiManager.layersDownloaded.textContent = "-";
    this.uiManager.totalDownloaded.textContent = "-";
    
    // Clear log
    this.uiManager.downloadLog.innerHTML = '<div class="text-[var(--text-secondary)]">Download log will appear here...</div>';
    
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
    this.uiManager.progressPercentage.textContent = "0%";
    this.uiManager.downloadStage.textContent = "Error";
    this.uiManager.downloadResponse.textContent = message;
    this.uiManager.downloadResponse.classList.remove('hidden');
    this.uiManager.downloadProgress.classList.add('hidden');
    this.uiManager.downloadButton.disabled = false;
    this.uiManager.downloadButton.textContent = "Download";
  }

  showDownloadSuccess() {
    this.uiManager.progressBar.style.width = "100%";
    this.uiManager.progressPercentage.textContent = "100%";
    this.uiManager.downloadStage.textContent = "Complete";
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
      const messageContent = lastChild.querySelector('.message-content');
      const currentText = messageContent.innerHTML;
      const newText = this.formatSystemMessages(currentText + data);
      messageContent.innerHTML = newText;
      
      // Check for metrics and sources in the updated content
      this.processObservabilityData(newText, lastChild);
    } else {
      // Create new AI message
      const aiMessage = document.createElement('div');
      aiMessage.className = 'flex justify-start mb-4 ai-message';
      
      const aiMessageContent = document.createElement('div');
      aiMessageContent.className = 'bg-[var(--bg-tertiary)] text-[var(--text-primary)] p-3 rounded-lg whitespace-pre-wrap break-words max-w-[80%] message-content';
      aiMessageContent.innerHTML = this.formatSystemMessages(data);
      
      aiMessage.appendChild(aiMessageContent);
      this.uiManager.chatWindow.appendChild(aiMessage);
      
      // Check for metrics and sources in the new content
      this.processObservabilityData(data, aiMessage);
    }
    
    this.uiManager.autoScroll();
  }

  handleAIStreamComplete() {
    // Stream is complete, ensure loading state is cleared
    this.clearLoadingState();
  }

  clearLoadingState() {
    this.uiManager.setUserInputEnabled(true);
    this.uiManager.hideSpinner();
    this.isProcessing = false;
    this.selectedFilePath = "";
  }
  
  processObservabilityData(content, messageElement) {
    // Check if we already have observability displays
    const existingMetrics = messageElement.querySelector('.metrics-display');
    const existingSources = messageElement.querySelector('.sources-display');
    
    if (existingMetrics && existingSources) {
      return; // Already processed
    }
    
    // Create metrics display
    const metricsDisplay = this.createMetricsDisplay(content);
    if (metricsDisplay && !existingMetrics) {
      messageElement.insertAdjacentHTML('beforeend', metricsDisplay);
    }
    
    // Create sources display
    const sourcesDisplay = this.createSourcesDisplay(content);
    if (sourcesDisplay && !existingSources) {
      messageElement.insertAdjacentHTML('beforeend', sourcesDisplay);
    }
  }

  formatSystemMessages(text) {
    // Convert *text* to italic styling
    return text.replace(/\*([^*]+)\*/g, '<em style="font-style: italic; opacity: 0.7;">$1</em>');
  }
  
  setupObservabilityHandlers() {
    // Token usage toggle
    const showTokensCheckbox = document.getElementById('show-tokens');
    if (showTokensCheckbox) {
      showTokensCheckbox.addEventListener('change', (e) => {
        this.observabilitySettings.showTokens = e.target.checked;
        this.saveObservabilitySettings();
      });
    }
    
    // Source attribution toggle
    const showSourcesCheckbox = document.getElementById('show-sources');
    if (showSourcesCheckbox) {
      showSourcesCheckbox.addEventListener('change', (e) => {
        this.observabilitySettings.showSources = e.target.checked;
        this.saveObservabilitySettings();
      });
    }
    
    // Processing details toggle
    const showDetailsCheckbox = document.getElementById('show-details');
    if (showDetailsCheckbox) {
      showDetailsCheckbox.addEventListener('change', (e) => {
        this.observabilitySettings.showDetails = e.target.checked;
        this.saveObservabilitySettings();
      });
    }
  }
  
  loadObservabilitySettings() {
    try {
      const saved = localStorage.getItem('ace-observability-settings');
      if (saved) {
        this.observabilitySettings = { ...this.observabilitySettings, ...JSON.parse(saved) };
      }
      
      // Update UI checkboxes
      const showTokensCheckbox = document.getElementById('show-tokens');
      const showSourcesCheckbox = document.getElementById('show-sources');
      const showDetailsCheckbox = document.getElementById('show-details');
      
      if (showTokensCheckbox) showTokensCheckbox.checked = this.observabilitySettings.showTokens;
      if (showSourcesCheckbox) showSourcesCheckbox.checked = this.observabilitySettings.showSources;
      if (showDetailsCheckbox) showDetailsCheckbox.checked = this.observabilitySettings.showDetails;
      
    } catch (error) {
      console.error('Error loading observability settings:', error);
    }
  }
  
  saveObservabilitySettings() {
    try {
      localStorage.setItem('ace-observability-settings', JSON.stringify(this.observabilitySettings));
    } catch (error) {
      console.error('Error saving observability settings:', error);
    }
  }
  
  createMetricsDisplay(metricsText) {
    if (!this.observabilitySettings.showTokens) return '';
    
    // Extract metrics from text like "*METRICS: 1,234 tokens • 2.5s • 3 sources*"
    const metricsMatch = metricsText.match(/\*METRICS: (.*?)\*/);
    if (!metricsMatch) return '';
    
    const metrics = metricsMatch[1];
    return `
      <div class="metrics-display bg-[var(--bg-tertiary)] rounded-lg p-3 mt-2 text-sm">
        <div class="flex items-center space-x-2 text-[var(--accent)]">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
          </svg>
          <span class="font-medium">Metrics:</span>
          <span class="text-[var(--text-primary)]">${metrics}</span>
        </div>
      </div>
    `;
  }
  
  createSourcesDisplay(sourcesText) {
    if (!this.observabilitySettings.showSources) return '';
    
    // Extract sources from text like "*SOURCES USED:*" followed by source lines
    const sourcesMatch = sourcesText.match(/\*SOURCES USED:\*([\s\S]*?)(?=\n\n|$)/);
    if (!sourcesMatch) return '';
    
    const sourcesContent = sourcesMatch[1];
    const sourceLines = sourcesContent.split('\n').filter(line => line.trim().startsWith('*') && line.includes('Score:'));
    
    if (sourceLines.length === 0) return '';
    
    const sourcesHtml = sourceLines.map(line => {
      // Extract source info from "*1. Score: 0.856 • Page: 1 • This is the content...*"
      const match = line.match(/\*(\d+)\. Score: ([\d.]+) • Page: ([\w\s]+) • (.+?)\*/);
      if (match) {
        const [, index, score, page, content] = match;
        return `
          <div class="source-item bg-[var(--bg-tertiary)] rounded p-2 mb-2">
            <div class="flex items-center justify-between text-xs">
              <span class="text-[var(--accent)] font-medium">Source ${index}</span>
              <span class="text-[var(--text-secondary)]">Score: ${score}</span>
              <span class="text-[var(--text-secondary)]">Page: ${page}</span>
            </div>
            <div class="text-sm text-[var(--text-primary)] mt-1">${content}</div>
          </div>
        `;
      }
      return '';
    }).join('');
    
    return `
      <div class="sources-display mt-3">
        <div class="flex items-center space-x-2 text-[var(--accent)] mb-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
          </svg>
          <span class="font-medium">Sources Used:</span>
        </div>
        ${sourcesHtml}
      </div>
    `;
  }
}

// Export for use in other modules
window.ChatManager = ChatManager; 