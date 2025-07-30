class UIManager {
  constructor() {
    this.initElements();
    this.isUserScrolling = false;
    this.init();
  }

  initElements() {
    // Main navigation elements
    this.toggleButton = document.getElementById('toggle-settings');
    this.toggleText = document.getElementById('toggle-text');
    this.mainTab = document.getElementById('main-tab');
    this.settingsTab = document.getElementById('settings-tab');
    this.clearChatButton = document.getElementById('clear-chat');

    // Chat elements
    this.chatWindow = document.getElementById('chat-window');
    this.emptyState = document.getElementById('empty-state');
    this.loadingSpinner = document.getElementById('loading-spinner');

    // Input elements
    this.queryInput = document.getElementById('query-input');
    this.submitButton = document.getElementById('submit-button');
    this.modelSelect = document.getElementById('model-select');
    this.uploadButton = document.getElementById('upload-button');
    this.fileInput = document.getElementById('file-input');

    // Settings elements
    this.downloadButton = document.getElementById('download-button');
    this.modelDownloadInput = document.getElementById('model-download-input');
    this.downloadProgress = document.getElementById('download-progress');
    this.progressBar = document.getElementById('progress-bar');
    this.progressText = document.getElementById('progress-text');
    this.progressPercentage = document.getElementById('progress-percentage');
    this.downloadResponse = document.getElementById('download-response');
  }

  init() {
    this.setupScrollHandling();
    this.setupInputHandling();
    this.setupTabSwitching();
  }

  // Scroll handling
  setupScrollHandling() {
    this.chatWindow.addEventListener('scroll', () => {
      const threshold = 10;
      this.isUserScrolling = (this.chatWindow.scrollHeight - this.chatWindow.scrollTop - this.chatWindow.clientHeight) > threshold;
    });
  }

  autoScroll() {
    if (!this.isUserScrolling) {
      this.chatWindow.scrollTop = this.chatWindow.scrollHeight;
    }
  }

  // Input handling
  setupInputHandling() {
    // Auto-resize textarea
    this.queryInput.addEventListener('input', () => {
      this.queryInput.style.height = 'auto';
      this.queryInput.style.height = (this.queryInput.scrollHeight) + 'px';
    });

    // Enter key handling
    this.queryInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.submitButton.click();
      }
    });
  }

  // Tab switching
  setupTabSwitching() {
    this.toggleButton.addEventListener('click', () => {
      this.toggleTabs();
    });
  }

  toggleTabs() {
    if (this.settingsTab.classList.contains('hidden')) {
      // Show settings
      this.settingsTab.classList.remove('hidden');
      this.settingsTab.classList.add('flex');
      this.mainTab.classList.add('hidden');
      this.mainTab.classList.remove('flex');
      // Update button style for settings mode
      this.toggleButton.style.setProperty('background-color', 'var(--bg-tertiary)', 'important');
      this.toggleButton.style.setProperty('color', 'var(--accent)', 'important');
      this.toggleText.textContent = 'Chat';
    } else {
      // Show chat
      this.settingsTab.classList.add('hidden');
      this.settingsTab.classList.remove('flex');
      this.mainTab.classList.remove('hidden');
      this.mainTab.classList.add('flex');
      // Update button style for chat mode
      this.toggleButton.style.setProperty('background-color', 'var(--accent)', 'important');
      // Special handling for nostalgia theme contrast
      const isNostalgia = document.documentElement.classList.contains('nostalgia');
      this.toggleButton.style.setProperty('color', isNostalgia ? 'var(--bg-primary)' : 'white', 'important');
      this.toggleText.textContent = 'Settings';
    }
  }

  // UI state management
  setUserInputEnabled(enabled) {
    this.queryInput.disabled = !enabled;
    this.submitButton.disabled = !enabled;
    this.modelSelect.disabled = !enabled;
    this.uploadButton.disabled = !enabled;
    
    if (enabled) {
      this.submitButton.classList.remove('opacity-50');
      this.submitButton.classList.add('glow');
    } else {
      this.submitButton.classList.add('opacity-50');
      this.submitButton.classList.remove('glow');
    }
  }

  showSpinner() {
    this.loadingSpinner.classList.remove('hidden');
    // Position spinner at the bottom of chat
    this.loadingSpinner.style.order = '999';
    this.autoScroll();
  }
  
  hideSpinner() {
    this.loadingSpinner.classList.add('hidden');
  }

  hideEmptyState() {
    if (this.emptyState) {
      this.emptyState.style.display = 'none';
    }
  }

  showEmptyState() {
    if (this.emptyState) {
      this.emptyState.style.display = 'flex';
    }
  }

  // Model selection
  populateModelSelect(options) {
    this.modelSelect.innerHTML = '';
    options.forEach(opt => {
      const optionElem = document.createElement('option');
      optionElem.value = opt;
      optionElem.textContent = opt;
      this.modelSelect.appendChild(optionElem);
    });
  }

  // Download progress handling
  updateDownloadProgress(progress) {
    // Update progress bar
    this.progressBar.style.width = `${progress.progress}%`;
    
    // Update status text with enhanced information
    this.progressText.textContent = progress.status;
    
    // Update percentage display
    this.progressPercentage.textContent = `${progress.progress}%`;
    
    // Add stage-based styling
    this.progressBar.className = 'bg-[var(--accent)] h-2.5 rounded-full transition-all duration-300';
    
    // Color coding based on stage
    if (progress.stage === 'error') {
      this.progressBar.classList.add('bg-red-500');
    } else if (progress.stage === 'complete') {
      this.progressBar.classList.add('bg-green-500');
    } else if (progress.stage === 'downloading layers') {
      this.progressBar.classList.add('bg-blue-500');
    } else {
      this.progressBar.classList.add('bg-[var(--accent)]');
    }

    // Handle completion
    if (progress.progress === 100 || progress.stage === 'complete') {
      this.downloadResponse.textContent = "Model installed successfully!";
      this.downloadResponse.classList.remove('hidden');
      this.downloadProgress.classList.add('hidden');
      this.downloadButton.disabled = false;
      this.downloadButton.textContent = "Download";
    }
  }

  // Reset functions
  resetQueryInput() {
    this.queryInput.value = "";
    this.queryInput.style.height = 'auto';
  }

  clearChatWindow() {
    while (this.chatWindow.firstChild) {
      this.chatWindow.removeChild(this.chatWindow.firstChild);
    }
    
    // Re-add empty state
    const emptyState = document.createElement('div');
    emptyState.className = 'flex justify-center items-center h-full';
    emptyState.id = 'empty-state';
    emptyState.innerHTML = `
      <div class="text-center text-[var(--text-secondary)]">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
        <p class="text-lg">Start a conversation with ACE</p>
        <p class="text-sm mt-1">Ask anything or upload a file for analysis</p>
      </div>
    `;
    this.chatWindow.appendChild(emptyState);
    this.emptyState = emptyState;
    
    // Re-add loading spinner
    const loadingSpinner = document.createElement('div');
    loadingSpinner.id = 'loading-spinner';
    loadingSpinner.className = 'hidden flex justify-center items-center py-4';
    loadingSpinner.innerHTML = '<div class="w-8 h-8 border-4 border-[var(--accent)] border-t-transparent rounded-full animate-spin"></div>';
    this.chatWindow.appendChild(loadingSpinner);
    this.loadingSpinner = loadingSpinner;
  }
}

// Export for use in other modules
window.UIManager = UIManager; 