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
  
  // Event Listeners
  onAIStream: (callback) => {
    ipcRenderer.on('ai-stream', (event, data) => callback(data));
  },
  
  onDownloadProgress: (callback) => {
    ipcRenderer.on('download-progress', (event, progress) => callback(progress));
  },
  
  // Remove listeners to prevent memory leaks
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
}); 