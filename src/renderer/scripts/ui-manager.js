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
    this.fineTuneTab = document.getElementById('fine-tune-tab');
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

    // Fine-tuning elements
    this.fineTuneButton = document.getElementById('fine-tune-button');
    this.checkIcon = document.getElementById('check-icon');
    this.checkStatus = document.getElementById('check-status');
    this.ramInfo = document.getElementById('ram-info');
    this.gpuInfo = document.getElementById('gpu-info');
    this.storageInfo = document.getElementById('storage-info');
    this.baseModelSelect = document.getElementById('base-model-select');
    this.uploadTrainingData = document.getElementById('upload-training-data');
    this.trainingDataInput = document.getElementById('training-data-input');
    this.trainingFilesList = document.getElementById('training-files-list');
    this.learningRate = document.getElementById('learning-rate');
    this.epochs = document.getElementById('epochs');
    this.batchSize = document.getElementById('batch-size');
    this.fineTunedModelName = document.getElementById('fine-tuned-model-name');
    this.startFineTuning = document.getElementById('start-fine-tuning');
    this.trainingProgress = document.getElementById('training-progress');
    this.trainingProgressBar = document.getElementById('training-progress-bar');
    this.trainingProgressPercentage = document.getElementById('training-progress-percentage');
    this.currentEpoch = document.getElementById('current-epoch');
    this.timeElapsed = document.getElementById('time-elapsed');
    this.currentLoss = document.getElementById('current-loss');
    this.eta = document.getElementById('eta');
    this.trainingLog = document.getElementById('training-log');
    
    // Model management elements
    this.refreshModelsButton = document.getElementById('refresh-models');
    this.modelsList = document.getElementById('models-list');
    this.noModelsMessage = document.getElementById('no-models');
  }

  init() {
    this.setupScrollHandling();
    this.setupInputHandling();
    this.setupTabSwitching();
    this.setupFineTuning();
    this.setupModelManagement();
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
    if (this.settingsTab.classList.contains('hidden') && this.fineTuneTab.classList.contains('hidden')) {
      // Show settings
      this.settingsTab.classList.remove('hidden');
      this.settingsTab.classList.add('flex');
      this.mainTab.classList.add('hidden');
      this.mainTab.classList.remove('flex');
      this.fineTuneTab.classList.add('hidden');
      this.fineTuneTab.classList.remove('flex');
      // Update button styles
      this.toggleButton.style.setProperty('background-color', 'var(--bg-tertiary)', 'important');
      this.toggleButton.style.setProperty('color', 'var(--accent)', 'important');
      this.toggleText.textContent = 'Chat';
      this.fineTuneButton.style.setProperty('background-color', 'var(--bg-tertiary)', 'important');
      this.fineTuneButton.style.setProperty('color', 'var(--accent)', 'important');
      // Hide clear chat button on settings, show fine-tune button
      this.clearChatButton.style.display = 'none';
      this.fineTuneButton.style.display = 'block';
    } else {
      // Show chat
      this.settingsTab.classList.add('hidden');
      this.settingsTab.classList.remove('flex');
      this.fineTuneTab.classList.add('hidden');
      this.fineTuneTab.classList.remove('flex');
      this.mainTab.classList.remove('hidden');
      this.mainTab.classList.add('flex');
      // Update button styles
      this.toggleButton.style.setProperty('background-color', 'var(--accent)', 'important');
      // Special handling for nostalgia theme contrast
      const isNostalgia = document.documentElement.classList.contains('nostalgia');
      this.toggleButton.style.setProperty('color', isNostalgia ? 'var(--bg-primary)' : 'white', 'important');
      this.toggleText.textContent = 'Settings';
      this.fineTuneButton.style.setProperty('background-color', 'var(--bg-tertiary)', 'important');
      this.fineTuneButton.style.setProperty('color', 'var(--accent)', 'important');
      // Show clear chat button and fine-tune button on main tab
      this.clearChatButton.style.display = 'block';
      this.fineTuneButton.style.display = 'block';
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

  // Fine-tuning setup
  setupFineTuning() {
    // Open fine-tuning tab
    this.fineTuneButton.addEventListener('click', () => {
      this.openFineTuneTab();
    });

    // Setup training data upload
    this.uploadTrainingData.addEventListener('click', () => {
      this.trainingDataInput.click();
    });

    this.trainingDataInput.addEventListener('change', (e) => {
      this.handleTrainingFiles(e.target.files);
    });

    // Setup start training button
    this.startFineTuning.addEventListener('click', () => {
      this.startFineTuningProcess();
    });
  }

  openFineTuneTab() {
    // Hide all tabs
    this.mainTab.classList.add('hidden');
    this.mainTab.classList.remove('flex');
    this.settingsTab.classList.add('hidden');
    this.settingsTab.classList.remove('flex');
    this.fineTuneTab.classList.remove('hidden');
    this.fineTuneTab.classList.add('flex');
    
    // Update button styles
    this.toggleButton.style.setProperty('background-color', 'var(--bg-tertiary)', 'important');
    this.toggleButton.style.setProperty('color', 'var(--accent)', 'important');
    this.toggleText.textContent = 'Chat';
    this.fineTuneButton.style.setProperty('background-color', 'var(--accent)', 'important');
    this.fineTuneButton.style.setProperty('color', 'white', 'important');
    
    // Hide clear chat button and fine-tune button on fine-tuning tab
    this.clearChatButton.style.display = 'none';
    this.fineTuneButton.style.display = 'none';
    
    // Check system requirements when tab opens
    this.checkSystemRequirements();
  }

  async checkSystemRequirements() {
    try {
      this.checkStatus.textContent = 'Checking system requirements...';
      this.checkIcon.innerHTML = '<svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';

      // Always populate models first, regardless of system check
      this.populateBaseModelSelect();

      // Set default values immediately
      this.ramInfo.textContent = 'Checking...';
      this.gpuInfo.textContent = 'Checking...';
      this.storageInfo.textContent = 'Checking...';
      
      // Update capabilities with default values while checking
      this.updateCapabilitiesAndLimitations({
        ram_gb: 16, // Conservative default
        storage_gb: 20, // Conservative default
        gpu_available: false,
        gpu_memory_gb: 0,
        can_fine_tune: true // Assume compatible by default
      });

      const requirements = await window.electronAPI.checkSystemRequirements();
      
      // Update system details
      this.ramInfo.textContent = `${requirements.ram_gb.toFixed(1)}GB`;
      this.gpuInfo.textContent = requirements.gpu_available ? `${requirements.gpu_memory_gb.toFixed(1)}GB VRAM` : 'Not available';
      this.storageInfo.textContent = `${requirements.storage_gb.toFixed(1)}GB available`;

      // Update status based on compatibility
      if (requirements.can_fine_tune) {
        this.checkStatus.textContent = 'System compatible for fine-tuning!';
        this.checkIcon.innerHTML = '<svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
        this.startFineTuning.disabled = false;
      } else {
        this.checkStatus.textContent = 'System not compatible for fine-tuning';
        this.checkIcon.innerHTML = '<svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';
        this.startFineTuning.disabled = true;
      }

      // Update capabilities and limitations with actual values
      this.updateCapabilitiesAndLimitations(requirements);
    } catch (error) {
      console.error('Error checking system requirements:', error);
      this.checkStatus.textContent = 'System check failed - models still available';
      this.checkIcon.innerHTML = '<svg class="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path></svg>';
      
      // Set default values if system check fails
      this.ramInfo.textContent = 'Unknown';
      this.gpuInfo.textContent = 'Unknown';
      this.storageInfo.textContent = 'Unknown';
      
      // Still allow fine-tuning but with warning
      this.startFineTuning.disabled = false;
      
      // Update capabilities with conservative defaults
      this.updateCapabilitiesAndLimitations({
        ram_gb: 8, // Conservative default
        storage_gb: 10, // Conservative default
        gpu_available: false,
        gpu_memory_gb: 0,
        can_fine_tune: true // Assume compatible
      });
    }
  }

  updateCapabilitiesAndLimitations(requirements) {
    const capabilitiesContainer = document.querySelector('#fine-tune-tab .bg-green-900\\/20 ul');
    const limitationsContainer = document.querySelector('#fine-tune-tab .bg-red-900\\/20 ul');
    
    if (!capabilitiesContainer || !limitationsContainer) return;

    // Clear existing content
    capabilitiesContainer.innerHTML = '';
    limitationsContainer.innerHTML = '';

    // Dynamic capabilities based on hardware
    const capabilities = [];
    const limitations = [];

    // RAM-based capabilities
    if (requirements.ram_gb >= 32) {
      capabilities.push('<strong>High-performance fine-tuning</strong> (32GB+ RAM available)');
      capabilities.push('<strong>Large datasets</strong> (1000+ examples possible)');
    } else if (requirements.ram_gb >= 16) {
      capabilities.push('<strong>Standard fine-tuning</strong> (16GB+ RAM available)');
      capabilities.push('<strong>Medium datasets</strong> (500-1000 examples)');
    } else if (requirements.ram_gb >= 8) {
      capabilities.push('<strong>Basic fine-tuning</strong> (8GB+ RAM available)');
      capabilities.push('<strong>Small datasets</strong> (100-500 examples)');
    } else {
      limitations.push('<strong>Insufficient RAM</strong> (requires 8GB+, you have ' + requirements.ram_gb.toFixed(1) + 'GB)');
    }

    // GPU-based capabilities
    if (requirements.gpu_available) {
      capabilities.push('<strong>GPU acceleration</strong> (' + requirements.gpu_memory_gb.toFixed(1) + 'GB VRAM)');
      capabilities.push('<strong>Faster training</strong> (2-4 hours typical)');
    } else {
      limitations.push('<strong>No GPU acceleration</strong> (CPU-only training, 4-8 hours typical)');
    }

    // Storage-based capabilities
    if (requirements.storage_gb >= 20) {
      capabilities.push('<strong>Ample storage</strong> (' + requirements.storage_gb.toFixed(1) + 'GB available)');
    } else if (requirements.storage_gb >= 10) {
      capabilities.push('<strong>Sufficient storage</strong> (' + requirements.storage_gb.toFixed(1) + 'GB available)');
    } else {
      limitations.push('<strong>Limited storage</strong> (requires 5GB+, you have ' + requirements.storage_gb.toFixed(1) + 'GB)');
    }

    // Universal capabilities (if system can fine-tune)
    if (requirements.can_fine_tune) {
      capabilities.push('<strong>LoRA fine-tuning</strong> on 7B parameter models');
      capabilities.push('<strong>Domain adaptation</strong> for specific use cases');
      capabilities.push('<strong>Compact storage</strong> (~100MB adapter files)');
    }

    // Universal limitations
    limitations.push('<strong>No full fine-tuning</strong> (requires 40GB+ VRAM)');
    limitations.push('<strong>Limited to 7B models</strong> (no 13B+ models)');
    limitations.push('<strong>Data quality dependent</strong> (garbage in = garbage out)');
    limitations.push('<strong>No real-time training</strong> (batch process only)');

    // Render capabilities
    capabilities.forEach(capability => {
      const li = document.createElement('li');
      li.className = 'flex items-start';
      li.innerHTML = `<span class="text-green-400 mr-2">•</span><span>${capability}</span>`;
      capabilitiesContainer.appendChild(li);
    });

    // Render limitations
    limitations.forEach(limitation => {
      const li = document.createElement('li');
      li.className = 'flex items-start';
      li.innerHTML = `<span class="text-red-400 mr-2">•</span><span>${limitation}</span>`;
      limitationsContainer.appendChild(li);
    });
  }

  async populateBaseModelSelect() {
    try {
      const models = await window.electronAPI.getAIOptions();
      
      // Show all available models instead of filtering
      this.baseModelSelect.innerHTML = '<option value="">Choose a model to fine-tune...</option>';
      models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        this.baseModelSelect.appendChild(option);
      });
      
      // Add a note about model compatibility (only if not already added)
      const existingNote = this.baseModelSelect.parentNode.querySelector('.model-compatibility-note');
      if (models.length > 0 && !existingNote) {
        const note = document.createElement('p');
        note.className = 'text-xs text-[var(--text-secondary)] mt-2 model-compatibility-note';
        note.textContent = 'Note: All models can be fine-tuned, but smaller models (3B) will be faster than larger ones (7B+).';
        this.baseModelSelect.parentNode.appendChild(note);
      }
    } catch (error) {
      console.error('Error populating base model select:', error);
    }
  }

  handleTrainingFiles(files) {
    this.trainingFilesList.innerHTML = '';
    Array.from(files).forEach(file => {
      const fileItem = document.createElement('div');
      fileItem.className = 'flex items-center justify-between p-2 bg-[var(--bg-primary)] rounded';
      
      // Calculate file size with better precision
      const sizeInBytes = file.size;
      const sizeInMB = sizeInBytes / (1024 * 1024);
      const sizeDisplay = sizeInMB < 0.01 ? `${(sizeInBytes / 1024).toFixed(2)}KB` : `${sizeInMB.toFixed(2)}MB`;
      
      fileItem.innerHTML = `
        <span class="text-sm">${file.name}</span>
        <span class="text-xs text-[var(--text-secondary)]">${sizeDisplay}</span>
      `;
      this.trainingFilesList.appendChild(fileItem);
      
      // Debug log
      console.log(`File: ${file.name}, Size: ${sizeInBytes} bytes (${sizeDisplay})`);
    });
  }

  async startFineTuningProcess() {
    const baseModel = this.baseModelSelect.value;
    const modelName = this.fineTunedModelName.value;
    const learningRate = parseFloat(this.learningRate.value);
    const epochs = parseInt(this.epochs.value);
    const batchSize = parseInt(this.batchSize.value);
    const files = this.trainingDataInput.files;

    if (!baseModel || !modelName || !files.length) {
      alert('Please fill in all required fields and upload training data.');
      return;
    }

    try {
      this.startFineTuning.disabled = true;
      this.startFineTuning.textContent = 'Starting...';
      this.trainingProgress.classList.remove('hidden');

      // Show initial progress
      this.updateTrainingProgress({
        percentage: 0,
        currentEpoch: 'Preparing...',
        timeElapsed: '0:00',
        currentLoss: '-',
        eta: 'Calculating...',
        log: 'Starting fine-tuning process...'
      });

      // Convert files to serializable format
      const fileData = [];
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileContent = await this.readFileAsText(file);
        
        console.log(`Processing file: ${file.name}`);
        console.log(`Original size: ${file.size} bytes`);
        console.log(`Content length: ${fileContent.length} characters`);
        
        fileData.push({
          name: file.name,
          content: fileContent,
          size: file.size, // Preserve original file size in bytes
          type: file.type
        });
      }

      const result = await window.electronAPI.startFineTuning({
        baseModel,
        modelName,
        learningRate,
        epochs,
        batchSize,
        files: fileData
      });

      if (result.success) {
        this.updateTrainingProgress({
          percentage: 100,
          currentEpoch: 'Complete',
          timeElapsed: 'Done',
          currentLoss: 'Final',
          eta: 'Complete',
          log: result.message
        });
        
        this.startFineTuning.textContent = 'Training Complete';
        this.startFineTuning.disabled = true;
        
        // Show success message
        this.showModelManagementMessage('success', result.message);
        
        // Option to export to Ollama
        if (confirm('Fine-tuning completed! Would you like to export this model to Ollama?')) {
          this.exportFineTunedModel(modelName);
        }
      } else {
        this.updateTrainingProgress({
          percentage: 0,
          currentEpoch: 'Error',
          timeElapsed: 'Failed',
          currentLoss: 'Error',
          eta: 'Failed',
          log: 'Error: ' + result.error
        });
        
        alert('Failed to start fine-tuning: ' + result.error);
        this.startFineTuning.disabled = false;
        this.startFineTuning.textContent = 'Start Fine-Tuning Process';
      }
    } catch (error) {
      console.error('Error starting fine-tuning:', error);
      alert('Error starting fine-tuning: ' + error.message);
      this.startFineTuning.disabled = false;
      this.startFineTuning.textContent = 'Start Fine-Tuning Process';
    }
  }

  async exportFineTunedModel(modelName) {
    try {
      const result = await window.electronAPI.exportFineTunedModel(modelName);
      
      if (result.success) {
        this.showModelManagementMessage('success', result.message);
        
        // Refresh model lists
        this.loadModelsList();
        const options = await window.electronAPI.getAIOptions();
        this.populateModelSelect(options);
      } else {
        this.showModelManagementMessage('error', result.error);
      }
    } catch (error) {
      console.error('Error exporting model:', error);
      this.showModelManagementMessage('error', 'Failed to export model');
    }
  }

  updateTrainingProgress(progress) {
    this.trainingProgressBar.style.width = `${progress.percentage}%`;
    this.trainingProgressPercentage.textContent = `${progress.percentage}%`;
    this.currentEpoch.textContent = progress.currentEpoch || '-';
    this.timeElapsed.textContent = progress.timeElapsed || '-';
    this.currentLoss.textContent = progress.currentLoss || '-';
    this.eta.textContent = progress.eta || '-';
    
    if (progress.log) {
      this.trainingLog.innerHTML += `<div>${progress.log}</div>`;
      this.trainingLog.scrollTop = this.trainingLog.scrollHeight;
    }
  }

  // Model Management Methods
  setupModelManagement() {
    this.refreshModelsButton.addEventListener('click', () => {
      this.loadModelsList();
    });
    
    // Load models when settings tab is opened
    this.toggleButton.addEventListener('click', () => {
      if (this.settingsTab.classList.contains('hidden')) {
        this.loadModelsList();
      }
    });
  }

  async loadModelsList() {
    try {
      this.modelsList.innerHTML = '<div class="text-center text-[var(--text-secondary)] py-4">Loading models...</div>';
      
      const models = await window.electronAPI.getModelInfo();
      
      if (models.length === 0) {
        this.modelsList.classList.add('hidden');
        this.noModelsMessage.classList.remove('hidden');
        return;
      }
      
      this.modelsList.classList.remove('hidden');
      this.noModelsMessage.classList.add('hidden');
      
      this.modelsList.innerHTML = '';
      
      models.forEach(model => {
        const modelCard = this.createModelCard(model);
        this.modelsList.appendChild(modelCard);
      });
      
    } catch (error) {
      console.error('Error loading models:', error);
      this.modelsList.innerHTML = '<div class="text-center text-[var(--text-secondary)] py-4">Error loading models</div>';
    }
  }

  createModelCard(model) {
    const card = document.createElement('div');
    card.className = 'bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--bg-primary)]';
    
    const modifiedDate = model.modified !== 'Unknown' ? new Date(model.modified).toLocaleDateString() : 'Unknown';
    
    card.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <h4 class="font-semibold text-[var(--text-primary)] mb-1">${model.name}</h4>
          <div class="flex items-center space-x-4 text-sm text-[var(--text-secondary)]">
            <span>Size: ${model.size_gb} GB</span>
            <span>Modified: ${modifiedDate}</span>
          </div>
        </div>
        <button class="delete-model-btn bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition-all duration-200" data-model="${model.name}">
          Delete
        </button>
      </div>
    `;
    
    // Add delete event listener
    const deleteBtn = card.querySelector('.delete-model-btn');
    deleteBtn.addEventListener('click', () => {
      this.confirmDeleteModel(model.name);
    });
    
    return card;
  }

  async confirmDeleteModel(modelName) {
    const confirmed = confirm(`Are you sure you want to delete "${modelName}"?\n\nThis action cannot be undone and will free up ${this.getModelSize(modelName)} of storage space.`);
    
    if (confirmed) {
      try {
        const result = await window.electronAPI.deleteModel(modelName);
        
        if (result.status === 'success') {
          // Refresh the models list
          this.loadModelsList();
          
          // Also refresh the model select dropdown
          try {
            const options = await window.electronAPI.getAIOptions();
            this.populateModelSelect(options);
          } catch (error) {
            console.error('Error refreshing model select:', error);
          }
          
          // Show success message
          this.showModelManagementMessage('success', result.message);
        } else {
          this.showModelManagementMessage('error', result.message);
        }
      } catch (error) {
        console.error('Error deleting model:', error);
        this.showModelManagementMessage('error', 'Failed to delete model');
      }
    }
  }

  getModelSize(modelName) {
    // This is a placeholder - in a real implementation, you'd get the actual size
    return '~2-8 GB';
  }

  readFileAsText(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(e);
      reader.readAsText(file);
    });
  }

  showModelManagementMessage(type, message) {
    // Create a temporary message element
    const messageEl = document.createElement('div');
    messageEl.className = `fixed top-4 right-4 p-4 rounded-lg text-white z-50 transition-all duration-300 ${
      type === 'success' ? 'bg-green-600' : 'bg-red-600'
    }`;
    messageEl.textContent = message;
    
    document.body.appendChild(messageEl);
    
    // Remove after 3 seconds
    setTimeout(() => {
      messageEl.remove();
    }, 3000);
  }
}

// Export for use in other modules
window.UIManager = UIManager; 