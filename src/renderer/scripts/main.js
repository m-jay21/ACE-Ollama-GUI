// Main application initialization
class ACEApp {
  constructor() {
    this.init();
  }

  async init() {
    // Initialize all managers
    this.uiManager = new window.UIManager();
    this.themeManager = new window.ThemeManager();
    this.ipcHandlers = new window.IPCHandlers(null, this.uiManager); // chatManager will be set later
    this.chatManager = new window.ChatManager(this.uiManager, this.ipcHandlers);
    
    // Update IPC handlers with chat manager reference
    this.ipcHandlers.chatManager = this.chatManager;

    // Load initial data
    await this.loadInitialData();

    console.log('ACE application initialized successfully');
  }

  async loadInitialData() {
    try {
      // Load available AI models
      const options = await this.ipcHandlers.getAIOptions();
      this.uiManager.populateModelSelect(options);
    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const app = new ACEApp();
});

// Make app available globally for debugging
window.ACEApp = ACEApp; 