class ThemeManager {
  constructor() {
    this.themeSelect = document.getElementById('theme-select');
    this.init();
  }

  init() {
    // Initialize theme from localStorage or default to dark
    const savedTheme = localStorage.getItem('theme') || 'dark';
    this.themeSelect.value = savedTheme;
    this.setTheme(savedTheme);

    // Listen for theme changes
    this.themeSelect.addEventListener('change', (e) => {
      this.setTheme(e.target.value);
    });

    // Listen for system theme changes when in system mode
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (this.themeSelect.value === 'system') {
        this.setTheme('system');
      }
    });
  }

  setTheme(theme) {
    const html = document.documentElement;
    
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      html.classList.remove('dark', 'light', 'nostalgia', 'gold');
      html.classList.add(systemTheme);
    } else {
      html.classList.remove('dark', 'light', 'nostalgia', 'gold');
      html.classList.add(theme);
    }
    
    // Save theme preference
    localStorage.setItem('theme', theme);
    
    // Refresh button styles after theme change
    this.refreshButtonStyles();
  }

  refreshButtonStyles() {
    const toggleButton = document.getElementById('toggle-settings');
    const settingsTab = document.getElementById('settings-tab');
    
    if (toggleButton && settingsTab) {
      if (settingsTab.classList.contains('hidden')) {
        // Currently showing chat - button should show "Settings"
        toggleButton.style.setProperty('background-color', 'var(--accent)', 'important');
        // Special handling for nostalgia theme contrast
        const isNostalgia = document.documentElement.classList.contains('nostalgia');
        toggleButton.style.setProperty('color', isNostalgia ? 'var(--bg-primary)' : 'white', 'important');
      } else {
        // Currently showing settings - button should show "Chat"  
        toggleButton.style.setProperty('background-color', 'var(--bg-tertiary)', 'important');
        toggleButton.style.setProperty('color', 'var(--accent)', 'important');
      }
    }
  }

  getCurrentTheme() {
    return this.themeSelect.value;
  }
}

// Export for use in other modules
window.ThemeManager = ThemeManager; 