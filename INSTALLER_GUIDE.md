# ACE Local AI - Installer Guide

This guide explains how to build and distribute installers for ACE's Local AI application.

## Overview

ACE is designed to be packaged as a cross-platform installer with the following features:

- **Windows**: NSIS installer with desktop shortcuts and start menu integration
- **macOS**: DMG disk image with drag-and-drop installation
- **Linux**: AppImage and DEB package options

## Prerequisites

### Development Environment

1. **Node.js 16+** - Download from [nodejs.org](https://nodejs.org)
2. **Python 3.8+** - Download from [python.org](https://python.org)
3. **Git** - For version control

### Platform-Specific Requirements

#### Windows
- **Windows 10/11** (64-bit)
- **Visual Studio Build Tools** (for native modules)
- **NSIS** (included with electron-builder)

#### macOS
- **macOS 10.15+** (Catalina or later)
- **Xcode Command Line Tools** (`xcode-select --install`)
- **Code signing certificate** (for distribution)

#### Linux
- **Ubuntu 18.04+** or equivalent
- **Build essentials**: `sudo apt-get install build-essential`
- **Additional dependencies**: `sudo apt-get install libgtk-3-dev libwebkit2gtk-4.0-dev`

## Building the Installer

### 1. Clone and Setup

```bash
git clone https://github.com/m-jay21/ACE-Ollama-GUI.git
cd ACE-Ollama-GUI
```

### 2. Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Build the Installer

#### All Platforms
```bash
npm run dist
```

#### Platform-Specific Builds
```bash
# Windows
npm run dist:win

# macOS
npm run dist:mac

# Linux
npm run dist:linux
```

### 4. Find the Installer

The built installers will be in the `dist/` directory:

- **Windows**: `ACE's Local AI-v4.0.0-Windows.exe` (NSIS installer)
- **macOS**: `ACE's Local AI-4.0.0.dmg` (Disk image)
- **Linux**: `ACE's Local AI-4.0.0.AppImage` (Portable AppImage)

## Installer Features

### Windows Installer (NSIS)

- **Custom installation directory** - Users can choose where to install
- **Desktop shortcut** - Creates a desktop icon
- **Start menu integration** - Adds to Windows Start menu
- **Uninstaller** - Proper uninstallation through Control Panel
- **Portable option** - Also creates a portable executable

### macOS Installer (DMG)

- **Drag-and-drop installation** - Simple installation process
- **Applications folder integration** - Installs to /Applications
- **Code signing** - Can be signed for Gatekeeper compatibility
- **Universal binary** - Supports both Intel and Apple Silicon

### Linux Installer (AppImage)

- **Portable** - Runs without installation
- **Self-contained** - Includes all dependencies
- **Cross-distribution** - Works on most Linux distributions
- **DEB package** - Also creates a Debian package

## Distribution

### GitHub Releases

1. **Tag a release** in Git:
   ```bash
   git tag v4.0.0
   git push origin v4.0.0
   ```

2. **Upload installers** to GitHub Releases:
   - Go to GitHub repository
   - Click "Releases"
   - Create a new release with the tag
   - Upload the installer files

### Auto-Updates

The application includes auto-update functionality:

- **Automatic checks** - Checks for updates on startup
- **User notifications** - Informs users of available updates
- **Automatic download** - Downloads updates in the background
- **Restart to install** - Prompts user to restart for installation

## User Installation Guide

### Windows Users

1. **Download** the `.exe` installer
2. **Run** the installer as administrator
3. **Choose** installation directory (optional)
4. **Complete** installation
5. **Launch** ACE from Start menu or desktop shortcut

### macOS Users

1. **Download** the `.dmg` file
2. **Open** the disk image
3. **Drag** ACE to Applications folder
4. **Launch** from Applications folder
5. **First run** - May need to allow in Security & Privacy

### Linux Users

#### AppImage (Recommended)
1. **Download** the `.AppImage` file
2. **Make executable**: `chmod +x "ACE's Local AI-4.0.0.AppImage"`
3. **Run**: `./"ACE's Local AI-4.0.0.AppImage"`

#### DEB Package
1. **Download** the `.deb` file
2. **Install**: `sudo dpkg -i "ACE's Local AI-4.0.0.deb"`
3. **Launch** from application menu

## Dependencies

### Required for Users

- **Python 3.8+** - For AI processing
- **Ollama** - For local AI models
- **Internet connection** - For initial model downloads

### Optional for Users

- **GPU support** - For faster AI processing
- **8GB+ RAM** - For optimal performance
- **SSD storage** - For faster model loading

## Troubleshooting

### Build Issues

#### Windows
- **Visual Studio Build Tools**: Install from Microsoft
- **Python PATH**: Ensure Python is in system PATH
- **Node.js version**: Use Node.js 16+ for compatibility

#### macOS
- **Xcode Command Line Tools**: Run `xcode-select --install`
- **Code signing**: Set up certificates for distribution
- **Python**: Use Homebrew Python if needed

#### Linux
- **Build dependencies**: Install required packages
- **Python**: Ensure Python 3.8+ is available
- **Node.js**: Use NodeSource repository for latest version

### Runtime Issues

#### Python Not Found
- **Windows**: Add Python to PATH or reinstall
- **macOS**: Install Python from python.org
- **Linux**: Install Python 3.8+ from package manager

#### Ollama Not Found
- **Install Ollama**: Download from [ollama.ai](https://ollama.ai)
- **Start Ollama**: Run `ollama serve` in terminal
- **Check connection**: Verify Ollama is running on port 11434

#### Model Download Issues
- **Internet connection**: Check network connectivity
- **Disk space**: Ensure sufficient free space (5GB+)
- **Firewall**: Allow Ollama through firewall

## Advanced Configuration

### Custom Installer Settings

Edit `package.json` build configuration:

```json
{
  "build": {
    "appId": "com.ace.ollama",
    "productName": "ACE's Local AI",
    "directories": {
      "output": "dist"
    },
    "files": [
      "**/*",
      "!node_modules/**/*"
    ],
    "extraResources": [
      {
        "from": "src/backend",
        "to": "src/backend"
      }
    ]
  }
}
```

### Code Signing (macOS)

1. **Get certificate** from Apple Developer Program
2. **Configure** in `package.json`:
   ```json
   {
     "build": {
       "mac": {
         "identity": "Your Certificate Name"
       }
     }
   }
   ```

### Auto-Update Configuration

Configure auto-updates in `package.json`:

```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "m-jay21",
      "repo": "ACE-Ollama-GUI"
    }
  }
}
```

## Security Considerations

### Code Signing
- **Windows**: Use Authenticode certificate
- **macOS**: Use Apple Developer certificate
- **Linux**: Consider GPG signing for packages

### Sandboxing
- **macOS**: Enable app sandboxing
- **Windows**: Use Windows Defender Application Control
- **Linux**: Consider AppArmor profiles

### Privacy
- **No telemetry**: Application doesn't collect user data
- **Local processing**: All AI processing happens locally
- **No external calls**: Except for model downloads

## Performance Optimization

### Installer Size
- **Exclude unnecessary files** from build
- **Compress resources** where possible
- **Use code splitting** for large dependencies

### Runtime Performance
- **Lazy loading** of heavy components
- **Background processing** for non-critical tasks
- **Memory management** with proper cleanup

## Testing

### Pre-Release Testing

1. **Build test** on target platforms
2. **Installation test** on clean systems
3. **Functionality test** with different configurations
4. **Performance test** with various hardware

### User Testing

1. **Beta releases** for early feedback
2. **User surveys** for feature requests
3. **Bug reports** collection and triage
4. **Performance monitoring** in production

## Support

### For Developers
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check README.md and code comments
- **Community**: Join discussions for help

### For Users
- **Installation guide**: This document
- **User manual**: Application help system
- **Troubleshooting**: Built-in error messages
- **Community support**: GitHub discussions

---

**ACE Local AI** - Making powerful AI accessible to everyone with privacy and control.
