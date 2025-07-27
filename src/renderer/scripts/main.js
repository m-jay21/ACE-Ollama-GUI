// Main application initialization
class ACEApp {
  constructor() {
    this.init();
  }

  async init() {
    try {
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
    } catch (error) {
      console.error('Error initializing ACE application:', error);
      this.showInitializationError(error);
    }
  }

  async loadInitialData() {
    try {
      // Load available AI models
      const options = await this.ipcHandlers.getAIOptions();
      this.uiManager.populateModelSelect(options);
      
      // Check if we have any models
      if (options.length === 0 || (options.length === 1 && options[0] === "No models found")) {
        console.warn('No AI models found. User will need to install models.');
      }
    } catch (error) {
      console.error('Error loading initial data:', error);
      // Don't throw here, just log the error
    }
  }

  showInitializationError(error) {
    // Create an error message in the UI
    const errorDiv = document.createElement('div');
    errorDiv.className = 'fixed inset-0 bg-red-900 bg-opacity-50 flex items-center justify-center z-50';
    errorDiv.innerHTML = `
      <div class="bg-white p-6 rounded-lg max-w-md mx-4">
        <h2 class="text-xl font-bold text-red-600 mb-4">Initialization Error</h2>
        <p class="text-gray-700 mb-4">Failed to initialize the application. Please restart the app.</p>
        <p class="text-sm text-gray-500 mb-4">Error: ${error.message}</p>
        <button onclick="window.location.reload()" class="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">
          Reload Application
        </button>
      </div>
    `;
    document.body.appendChild(errorDiv);
  }

  cleanup() {
    try {
      // Clean up IPC handlers
      if (this.ipcHandlers && typeof this.ipcHandlers.cleanup === 'function') {
        this.ipcHandlers.cleanup();
      }
      
      console.log('ACE application cleanup completed');
    } catch (error) {
      console.error('Error during cleanup:', error);
    }
  }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const app = new ACEApp();
  
  // Handle page unload for cleanup
  window.addEventListener('beforeunload', () => {
    if (app && typeof app.cleanup === 'function') {
      app.cleanup();
    }
  });
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  event.preventDefault();
});

// Handle global errors
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
});

// Make app available globally for debugging
window.ACEApp = ACEApp; 