const { contextBridge, ipcRenderer } = require('electron');

// SECURITY: Expose only the necessary APIs to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // AI Operations
  getAIOptions: () => ipcRenderer.invoke('get-ai-options'),
  submitAIQuery: (args) => ipcRenderer.invoke('submit-ai-query', args),
  downloadModel: (modelName) => ipcRenderer.invoke('download-model', modelName),
  
  // File Operations
  openFileDialog: () => ipcRenderer.invoke('open-file-dialog'),
  
  // Chat Operations
  clearChat: () => ipcRenderer.invoke('clear-chat'),
  
  // Fine-Tuning Operations
  checkSystemRequirements: () => ipcRenderer.invoke('check-system-requirements'),
  startFineTuning: (args) => ipcRenderer.invoke('start-fine-tuning', args),
  exportFineTunedModel: (modelName) => ipcRenderer.invoke('export-fine-tuned-model', modelName),
  
  // Model Management Operations
  getModelInfo: () => ipcRenderer.invoke('get-model-info'),
  deleteModel: (modelName) => ipcRenderer.invoke('delete-model', modelName),
  
  // Event Listeners
  onAIStream: (callback) => {
    ipcRenderer.on('ai-stream', (event, data) => callback(data));
  },
  
  onDownloadProgress: (callback) => {
    ipcRenderer.on('download-progress', (event, progress) => callback(progress));
  },
  
  onFineTuningProgress: (callback) => {
    ipcRenderer.on('fine-tuning-progress', (event, progress) => callback(progress));
  },
  
  // Remove listeners to prevent memory leaks
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
}); 