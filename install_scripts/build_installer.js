#!/usr/bin/env node
/**
 * Build script for ACE's Local AI installer
 * This script helps prepare the application for packaging
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('ACE Local AI - Installer Build Script');
console.log('=====================================');

// Check if we're in the right directory
if (!fs.existsSync('package.json')) {
  console.error('Error: package.json not found. Please run this script from the project root.');
  process.exit(1);
}

// Check if node_modules exists
if (!fs.existsSync('node_modules')) {
  console.log('Installing Node.js dependencies...');
  try {
    execSync('npm install', { stdio: 'inherit' });
  } catch (error) {
    console.error('Failed to install Node.js dependencies:', error.message);
    process.exit(1);
  }
}

// Check if requirements.txt exists
if (!fs.existsSync('requirements.txt')) {
  console.error('Error: requirements.txt not found.');
  process.exit(1);
}

// Create necessary directories
const dirs = ['install_scripts', 'python_installer'];
dirs.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    console.log(`Created directory: ${dir}`);
  }
});

// Copy requirements.txt to install_scripts
if (fs.existsSync('requirements.txt')) {
  fs.copyFileSync('requirements.txt', 'install_scripts/requirements.txt');
  console.log('Copied requirements.txt to install_scripts/');
}

// Check Python installation
console.log('\nChecking Python installation...');
try {
  const pythonVersion = execSync('python --version', { encoding: 'utf8' });
  console.log(`✓ Python found: ${pythonVersion.trim()}`);
} catch (error) {
  console.log('⚠ Python not found in PATH. Users will need to install Python manually.');
}

// Check if Ollama is available
console.log('\nChecking Ollama installation...');
try {
  const ollamaVersion = execSync('ollama --version', { encoding: 'utf8' });
  console.log(`✓ Ollama found: ${ollamaVersion.trim()}`);
} catch (error) {
  console.log('⚠ Ollama not found. Users will need to install Ollama from https://ollama.ai');
}

// Create a simple Python installer script
const pythonInstallerScript = `#!/usr/bin/env python3
"""
Python installer for ACE's Local AI
This script helps users install Python dependencies
"""

import sys
import subprocess
import os

def install_requirements():
    """Install Python requirements"""
    try:
        # Get the path to requirements.txt
        if getattr(sys, 'frozen', False):
            # Running in a bundle
            base_path = os.path.dirname(sys.executable)
            if os.name == 'nt':  # Windows
                base_path = os.path.join(base_path, '..', 'Resources')
            requirements_path = os.path.join(base_path, 'requirements.txt')
        else:
            # Development mode
            requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
        
        if not os.path.exists(requirements_path):
            print(f"ERROR: requirements.txt not found at {requirements_path}")
            return False
        
        print(f"Installing requirements from {requirements_path}")
        
        # Install requirements
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', requirements_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Requirements installed successfully")
            return True
        else:
            print(f"ERROR: Failed to install requirements: {result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to install requirements: {e}")
        return False

if __name__ == "__main__":
    success = install_requirements()
    sys.exit(0 if success else 1)
`;

fs.writeFileSync('install_scripts/install_python_deps.py', pythonInstallerScript);
console.log('Created Python dependency installer script');

// Create a README for the installer
const installerReadme = `# ACE Local AI - Installer

This directory contains scripts and resources for building the ACE Local AI installer.

## Files

- \`check_dependencies.py\` - Checks and installs Python dependencies
- \`install_python_deps.py\` - Python dependency installer
- \`requirements.txt\` - Python requirements (copied from project root)

## Building the Installer

1. Ensure all dependencies are installed:
   \`\`\`bash
   npm install
   pip install -r requirements.txt
   \`\`\`

2. Build the installer:
   \`\`\`bash
   npm run dist
   \`\`\`

3. Find the installer in the \`dist/\` directory

## Platform-Specific Builds

- Windows: \`npm run dist:win\`
- macOS: \`npm run dist:mac\`
- Linux: \`npm run dist:linux\`

## Requirements

- Node.js 16+
- Python 3.8+
- Ollama (for AI functionality)
- Electron Builder
- Platform-specific build tools

## Troubleshooting

If the build fails:

1. Check that all dependencies are installed
2. Ensure Python is in your PATH
3. Verify that Ollama is installed (optional for build)
4. Check platform-specific requirements

For more information, see the main README.md file.
`;

fs.writeFileSync('install_scripts/README.md', installerReadme);
console.log('Created installer README');

console.log('\n✓ Installer build preparation completed!');
console.log('\nTo build the installer, run:');
console.log('  npm run dist');
console.log('\nFor platform-specific builds:');
console.log('  npm run dist:win    # Windows');
console.log('  npm run dist:mac    # macOS');
console.log('  npm run dist:linux  # Linux');
