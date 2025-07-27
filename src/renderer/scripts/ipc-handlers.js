class IPCHandlers {
  constructor(chatManager, uiManager) {
    this.chatManager = chatManager;
    this.uiManager = uiManager;
    this.init();
  }

  init() {
    // Listen for AI streaming responses using the secure API
    window.electronAPI.onAIStream((data) => {
      this.chatManager.handleAIStream(data);
    });

    // Listen for model download progress using the secure API
    window.electronAPI.onDownloadProgress((progress) => {
      this.uiManager.updateDownloadProgress(progress);
    });
  }

  // AI Operations
  async getAIOptions() {
    try {
      return await window.electronAPI.getAIOptions();
    } catch (error) {
      console.error("Error fetching AI options:", error);
      return ["No models found"];
    }
  }

  async submitAIQuery(query, model, filePath = '') {
    try {
      return await window.electronAPI.submitAIQuery({
        query,
        model,
        filePath
      });
    } catch (error) {
      console.error("Error in AI query:", error);
      throw error;
    }
  }

  async downloadModel(modelName) {
    try {
      return await window.electronAPI.downloadModel(modelName);
    } catch (error) {
      console.error("Error downloading model:", error);
      throw error;
    }
  }

  // File Operations
  async openFileDialog() {
    try {
      return await window.electronAPI.openFileDialog();
    } catch (error) {
      console.error("Error opening file dialog:", error);
      return null;
    }
  }

  // Chat Operations
  async clearChat() {
    try {
      return await window.electronAPI.clearChat();
    } catch (error) {
      console.error('Error clearing chat:', error);
      throw error;
    }
  }

  // Cleanup method to remove listeners
  cleanup() {
    window.electronAPI.removeAllListeners('ai-stream');
    window.electronAPI.removeAllListeners('download-progress');
  }
}

// Export for use in other modules
window.IPCHandlers = IPCHandlers; 