# ACE Local AI - Installer

This directory contains scripts and resources for building the ACE Local AI installer.

## Files

- `check_dependencies.py` - Checks and installs Python dependencies
- `install_python_deps.py` - Python dependency installer
- `requirements.txt` - Python requirements (copied from project root)

## Building the Installer

1. Ensure all dependencies are installed:
   ```bash
   npm install
   pip install -r requirements.txt
   ```

2. Build the installer:
   ```bash
   npm run dist
   ```

3. Find the installer in the `dist/` directory

## Platform-Specific Builds

- Windows: `npm run dist:win`
- macOS: `npm run dist:mac`
- Linux: `npm run dist:linux`

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
