const { ipcRenderer } = require('electron');

class IPCHandlers {
  constructor(chatManager, uiManager) {
    this.chatManager = chatManager;
    this.uiManager = uiManager;
    this.init();
  }

  init() {
    // Listen for AI streaming responses
    ipcRenderer.on('ai-stream', (event, data) => {
      this.chatManager.handleAIStream(data);
    });

    // Listen for model download progress
    ipcRenderer.on('download-progress', (event, progress) => {
      this.uiManager.updateDownloadProgress(progress);
    });
  }

  // AI Operations
  async getAIOptions() {
    try {
      return await ipcRenderer.invoke('get-ai-options');
    } catch (error) {
      console.error("Error fetching AI options:", error);
      return ["No models found"];
    }
  }

  async submitAIQuery(query, model, filePath = '') {
    try {
      return await ipcRenderer.invoke('submit-ai-query', {
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
      return await ipcRenderer.invoke('download-model', modelName);
    } catch (error) {
      console.error("Error downloading model:", error);
      throw error;
    }
  }

  // File Operations
  async openFileDialog() {
    try {
      return await ipcRenderer.invoke('open-file-dialog');
    } catch (error) {
      console.error("Error opening file dialog:", error);
      return null;
    }
  }

  // Chat Operations
  async clearChat() {
    try {
      return await ipcRenderer.invoke('clear-chat');
    } catch (error) {
      console.error('Error clearing chat:', error);
      throw error;
    }
  }
}

// Export for use in other modules
window.IPCHandlers = IPCHandlers; 