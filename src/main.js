const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');

// Helper function to get the correct path for Python scripts
function getPythonScriptPath(scriptName) {
  if (app.isPackaged) {
    // In production, scripts are in the resources directory
    return path.join(process.resourcesPath, 'src', 'backend', scriptName);
  } else {
    // In development, scripts are in src/backend directory
    return path.join(__dirname, 'backend', scriptName);
  }
}

// Helper function to get Python executable path
function getPythonPath() {
  if (app.isPackaged) {
    // In production (packaged app), always use system Python
  if (process.platform === 'win32') {
      return 'python';
    } else {
      return 'python3';
    }
  } else {
    // In development, try virtual environment first, then fallback to system
    const venvPython = path.join(__dirname, '..', 'venv', 'bin', 'python');
    if (fs.existsSync(venvPython)) {
      console.log('Using virtual environment Python:', venvPython);
      return venvPython;
    } else {
      console.log('Virtual environment not found, using system Python');
      if (process.platform === 'win32') {
        return 'python';
      } else {
        return 'python3';
      }
    }
  }
}



// Helper function to validate Python installation
async function validatePythonInstallation() {
  return new Promise((resolve, reject) => {
    const pythonPath = getPythonPath();
    console.log('Using Python path:', pythonPath);
    
    // Test if Python can import the required modules
    const testProcess = spawn(pythonPath, ['-c', 'import ollama, pymupdf, PIL, tiktoken; print("All modules available")']);
    
    testProcess.on('close', (code) => {
      if (code === 0) {
        console.log('Python and all required modules validated successfully');
        resolve(true);
      } else {
        reject(new Error(`Python modules not available. Tried: ${pythonPath}. Exit code: ${code}`));
      }
    });
    
    testProcess.on('error', (error) => {
      reject(new Error(`Failed to execute Python. Tried: ${pythonPath}. Error: ${error.message}`));
    });
    
    testProcess.stderr.on('data', (data) => {
      console.error('Python validation stderr:', data.toString());
    });
    
    // Set a timeout
    setTimeout(() => {
      testProcess.kill();
      reject(new Error('Python validation timeout'));
    }, 10000);
  });
}

// Helper function to get the path for theMessages.txt
function getMessagesFilePath() {
  if (app.isPackaged) {
    // In production, use the resources directory
    return path.join(process.resourcesPath, 'src', 'data', 'theMessages.txt');
  } else {
    // In development, use the data directory within src
    return path.join(__dirname, 'data', 'theMessages.txt');
  }
}

// Helper function to get preload script path
function getPreloadScriptPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'src', 'renderer', 'preload.js');
  } else {
    return path.join(__dirname, 'renderer', 'preload.js');
  }
}

// Ensure theMessages.txt exists in the correct location
function ensureMessagesFileExists() {
  const messagesPath = getMessagesFilePath();
  const dataDir = path.dirname(messagesPath);
  
  // Ensure the data directory exists
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  // Ensure the messages file exists
  if (!fs.existsSync(messagesPath)) {
    fs.writeFileSync(messagesPath, '');
  }
}

// Helper function to check if Ollama is running
async function isOllamaRunning() {
  return new Promise((resolve) => {
    const req = http.get('http://127.0.0.1:11434/api/tags', (res) => {
      resolve(res.statusCode === 200);
    });
    
    req.on('error', () => {
      resolve(false);
    });
    
    req.setTimeout(3000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

// Helper function to start Ollama server
function startOllamaServer() {
  console.log('Starting Ollama server...');
  
  // Start Ollama in detached mode (background process)
  const ollamaProcess = spawn('ollama', ['serve'], {
    detached: true,
    stdio: 'ignore',
    windowsHide: true
  });
  
  // Don't wait for the process - let it run in background
  ollamaProcess.unref();
  
  console.log('Ollama server started in background');
  return ollamaProcess;
}

// Helper function to ensure Ollama is running
async function ensureOllamaRunning() {
  try {
    // First check if Ollama is already running
    if (await isOllamaRunning()) {
      console.log('Ollama server is already running');
      return true;
    }
    
    // Ollama not running - start it
    console.log('Ollama server not running, starting it...');
    startOllamaServer();
    
    // Wait for Ollama to start (check every 500ms for up to 10 seconds)
    for (let i = 0; i < 20; i++) {
      await new Promise(resolve => setTimeout(resolve, 500));
      if (await isOllamaRunning()) {
        console.log('Ollama server started successfully');
        return true;
      }
    }
    
    console.error('Failed to start Ollama server within timeout');
    return false;
  } catch (error) {
    console.error('Error ensuring Ollama is running:', error);
    return false;
  }
}

// Input validation and sanitization functions
function validateAndSanitizeInput(input, maxLength = 10000) {
  if (typeof input !== 'string') {
    throw new Error('Input must be a string');
  }
  
  if (input.length > maxLength) {
    throw new Error(`Input too long. Maximum length is ${maxLength} characters`);
  }
  
  // Remove null bytes and other dangerous characters
  return input.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
}

function validateAndSanitizeFilePath(filePath) {
  if (!filePath || typeof filePath !== 'string') {
    throw new Error('Invalid file path');
  }
  
  // Normalize the path to prevent path traversal attacks
  const normalizedPath = path.normalize(filePath);
  
  // Check for path traversal attempts
  if (normalizedPath.includes('..') || normalizedPath.includes('~')) {
    throw new Error('Invalid file path');
  }
  
  // Ensure the file exists
  if (!fs.existsSync(normalizedPath)) {
    throw new Error('File does not exist');
  }
  
  // Check file size (limit to 100MB)
  const stats = fs.statSync(normalizedPath);
  if (stats.size > 100 * 1024 * 1024) {
    throw new Error('File too large. Maximum size is 100MB');
  }
  
  return normalizedPath;
}

function validateModelName(modelName) {
  console.log('Validating model name:', JSON.stringify(modelName));
  console.log('Model name type:', typeof modelName);
  console.log('Model name length:', modelName ? modelName.length : 'null');
  
  if (!modelName || typeof modelName !== 'string') {
    throw new Error('Invalid model name');
  }
  
  // Only allow alphanumeric characters, hyphens, underscores, colons, and dots
  if (!/^[a-zA-Z0-9\-_:.]+$/.test(modelName)) {
    console.log('Model name failed regex test. Allowed chars: a-zA-Z0-9\\-_:.');
    throw new Error('Invalid model name format');
  }
  
  const trimmed = modelName.trim();
  console.log('Validated model name:', JSON.stringify(trimmed));
  return trimmed;
}

// Create the application window
function createWindow() {
  const win = new BrowserWindow({
    width: 960,
    height: 885,
    backgroundColor: '#0D4D66',  // Match your dark background
    autoHideMenuBar: true,       // Hide the menu bar by default
    webPreferences: {
      nodeIntegration: false,        // SECURITY: Disable node integration
      contextIsolation: true,        // SECURITY: Enable context isolation
      preload: getPreloadScriptPath(), // SECURITY: Use preload script for safe API exposure
      sandbox: false,                // Required for file system access
      webSecurity: true,             // SECURITY: Enable web security
    },
  });

  // Remove the default application menu completely
  Menu.setApplicationMenu(null);

  // Load your index.html file from renderer directory
  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

app.whenReady().then(async () => {
  try {
    // Validate Python installation
    await validatePythonInstallation();
    console.log('Python installation validated successfully');
    
    // Ensure Ollama is running
    await ensureOllamaRunning();
    
    // Ensure theMessages.txt exists when the app starts
    ensureMessagesFileExists();
    createWindow();

    // Re-create window on macOS when dock icon is clicked.
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  } catch (error) {
    console.error('Python validation failed:', error);
    
    // Create a window to show the error
    const errorWindow = new BrowserWindow({
      width: 600,
      height: 400,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: getPreloadScriptPath(),
      },
    });
    
    errorWindow.loadURL(`data:text/html,
      <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
          <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #e74c3c; margin-bottom: 20px;">Python Installation Error</h2>
            <p style="color: #333; margin-bottom: 15px;">ACE requires Python to be installed and accessible from the command line.</p>
            <p style="color: #666; margin-bottom: 20px;"><strong>Error:</strong> ${error.message}</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
              <h4 style="margin-top: 0;">To fix this:</h4>
              <ol style="margin: 0; padding-left: 20px;">
                <li>Install Python from <a href="https://python.org" target="_blank">python.org</a></li>
                <li>Make sure Python is added to your system PATH</li>
                <li>Restart the application</li>
              </ol>
            </div>
            <button onclick="window.close()" style="background: #e74c3c; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
              Close
            </button>
          </div>
        </body>
      </html>
    `);
  }
});

// Quit the app when all windows are closed (except on macOS).
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handler for opening a file dialog
ipcMain.handle('open-file-dialog', async (event) => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [
      { name: 'Documents', extensions: ['pdf', 'txt', 'md', 'csv', 'json', 'docx', 'doc'] },
      { name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'bmp', 'gif'] },
      { name: 'All Files', extensions: ['*'] }
    ],
  });
  if (result.canceled || result.filePaths.length === 0) {
    return null;
  }
  return result.filePaths[0];
});

// IPC handler for submitting an AI query
ipcMain.handle('submit-ai-query', async (event, args) => {
  try {
    // Validate and sanitize inputs
    const query = validateAndSanitizeInput(args.query, 50000); // Allow longer queries for AI
    const model = validateModelName(args.model);
    let filePath = null;
    
    if (args.filePath) {
      filePath = validateAndSanitizeFilePath(args.filePath);
    }

  return new Promise((resolve, reject) => {
      const scriptPath = getPythonScriptPath('run_ai.py');
    console.log('Python script path:', scriptPath);
    
    let scriptArgs = ['-u', scriptPath];

      // Pass validated query and model arguments to the Python script.
      scriptArgs.push('--query', query);
      scriptArgs.push('--model', model);

      // If a file was uploaded, pass its validated path and enable enhanced processing
      if (filePath) {
        scriptArgs.push('--file', filePath);
        // Enable semantic search with vector embeddings for best results
        scriptArgs.push('--use-semantic-search');
    }

      // Spawn the Python process with timeout
    const pythonProcess = spawn(getPythonPath(), scriptArgs);
      
      // Set timeout for the process (5 minutes)
      const timeout = setTimeout(() => {
        pythonProcess.kill('SIGTERM');
        reject(new Error('Request timeout - process took too long'));
      }, 5 * 60 * 1000);

    let fullResponse = '';

    // Stream data back to the renderer
    pythonProcess.stdout.on('data', (data) => {
      const text = data.toString();
      fullResponse += text;
      // Send each chunk back to the renderer for live update.
      event.sender.send('ai-stream', text);
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        if (code === 0) {
      resolve(fullResponse);
        } else {
          reject(new Error(`Python process exited with code ${code}`));
        }
      });

      pythonProcess.on('error', (error) => {
        clearTimeout(timeout);
        reject(new Error(`Failed to start Python process: ${error.message}`));
    });
  });
  } catch (error) {
    console.error('Error in submit-ai-query:', error);
    throw error;
  }
});

// IPC handler for downloading a model
ipcMain.handle('download-model', async (event, modelName) => {
  try {
    console.log('Download request for model:', JSON.stringify(modelName));
    // Validate and sanitize model name
    const validatedModelName = validateModelName(modelName);
    
  return new Promise((resolve, reject) => {
      const scriptPath = getPythonScriptPath('download_model.py');
    console.log('Python script path:', scriptPath);
    
    const scriptArgs = [
      '-u',
      scriptPath,
      '--model',
        validatedModelName,
    ];
      
    const pythonProcess = spawn(getPythonPath(), scriptArgs);
      
      // Set timeout for download process (30 minutes)
      const timeout = setTimeout(() => {
        pythonProcess.kill('SIGTERM');
        reject(new Error('Download timeout - process took too long'));
      }, 30 * 60 * 1000);

        pythonProcess.stdout.on('data', (data) => {
      data.toString().split('\n').forEach(line => {
        if (line.trim()) {
          try {
            const progress = JSON.parse(line);
            // Send progress to renderer
            event.sender.send('download-progress', progress);
            if (progress.progress === 100 || progress.status === "Cannot be installed" || progress.stage === "complete") {
              clearTimeout(timeout);
              resolve(progress);
            }
          } catch (e) {
            console.error('Error parsing download progress:', e, 'Raw line:', line);
            // Send error progress to frontend
            event.sender.send('download-progress', {
              status: "Error parsing progress data",
              progress: 0,
              stage: "error"
            });
          }
        }
      });
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error('Download stderr:', data.toString());
    });

    pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
      if (code !== 0) {
          reject(new Error(`Download process exited with code ${code}`));
      }
      });

      pythonProcess.on('error', (error) => {
        clearTimeout(timeout);
        reject(new Error(`Failed to start download process: ${error.message}`));
    });
  });
  } catch (error) {
    console.error('Error in download-model:', error);
    throw error;
  }
});

// IPC handler for retrieving AI model options
ipcMain.handle('get-ai-options', async () => {
  return new Promise((resolve, reject) => {
    const scriptPath = getPythonScriptPath('get_ai_options.py');
    console.log('Python script path:', scriptPath);
    
    const pythonProcess = spawn(getPythonPath(), [scriptPath]);
    let data = '';
    
    // Set timeout for the process (30 seconds)
    const timeout = setTimeout(() => {
      pythonProcess.kill('SIGTERM');
      console.error('get-ai-options timeout');
      resolve(["No models found"]);
    }, 30 * 1000);

    pythonProcess.stdout.on('data', (chunk) => {
      data += chunk;
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`get-ai-options stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
      clearTimeout(timeout);
      try {
        if (!data.trim()) {
          // If no data was received, return "No models found"
          resolve(["No models found"]);
          return;
        }
        const options = JSON.parse(data);
        resolve(options);
      } catch (err) {
        console.error('Error parsing AI options:', err);
        // Return "No models found" on error
        resolve(["No models found"]);
      }
    });

    pythonProcess.on('error', (err) => {
      clearTimeout(timeout);
      console.error('Error spawning Python process for get-ai-options:', err);
      // Return "No models found" on error
      resolve(["No models found"]);
    });
  });
});

// IPC handler for getting model information
ipcMain.handle('get-model-info', async () => {
  return new Promise((resolve, reject) => {
    const scriptPath = getPythonScriptPath('get_model_info.py');
    console.log('Python script path:', scriptPath);
    
    const pythonProcess = spawn(getPythonPath(), [scriptPath]);
    let data = '';
    
    const timeout = setTimeout(() => {
      pythonProcess.kill('SIGTERM');
      console.error('get-model-info timeout');
      resolve([]);
    }, 30 * 1000);

    pythonProcess.stdout.on('data', (chunk) => {
      data += chunk;
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`get-model-info stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
      clearTimeout(timeout);
      try {
        if (!data.trim()) {
          resolve([]);
          return;
        }
        const modelInfo = JSON.parse(data);
        resolve(modelInfo);
      } catch (err) {
        console.error('Error parsing model info:', err);
        resolve([]);
      }
    });

    pythonProcess.on('error', (err) => {
      clearTimeout(timeout);
      console.error('Error spawning Python process for get-model-info:', err);
      resolve([]);
    });
  });
});

// IPC handler for deleting a model
ipcMain.handle('delete-model', async (event, modelName) => {
  return new Promise((resolve, reject) => {
    try {
      const validatedModelName = validateModelName(modelName);
      const scriptPath = getPythonScriptPath('delete_model.py');
      console.log('Python script path:', scriptPath);
      
      const pythonProcess = spawn(getPythonPath(), [scriptPath, validatedModelName]);
      let data = '';
      
      const timeout = setTimeout(() => {
        pythonProcess.kill('SIGTERM');
        console.error('delete-model timeout');
        resolve({ status: 'error', message: 'Delete operation timed out' });
      }, 60 * 1000);

      pythonProcess.stdout.on('data', (chunk) => {
        data += chunk;
      });

      pythonProcess.stderr.on('data', (data) => {
        console.error(`delete-model stderr: ${data}`);
      });

      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        try {
          if (!data.trim()) {
            resolve({ status: 'error', message: 'No response from delete operation' });
            return;
          }
          const result = JSON.parse(data);
          resolve(result);
        } catch (err) {
          console.error('Error parsing delete result:', err);
          resolve({ status: 'error', message: 'Failed to parse delete result' });
        }
      });

      pythonProcess.on('error', (err) => {
        clearTimeout(timeout);
        console.error('Error spawning Python process for delete-model:', err);
        resolve({ status: 'error', message: 'Failed to start delete operation' });
      });
    } catch (error) {
      console.error('Error in delete-model:', error);
      resolve({ status: 'error', message: error.message });
    }
  });
});

// IPC handler for clearing chat
ipcMain.handle('clear-chat', async () => {
  return new Promise((resolve, reject) => {
    try {
      const messagesPath = getMessagesFilePath();
      console.log('Clearing chat file at:', messagesPath);
      fs.writeFileSync(messagesPath, '');
      resolve(true);
    } catch (error) {
      console.error('Error clearing chat:', error);
      reject(error);
    }
  });
});

// IPC handler for checking system requirements for fine-tuning
ipcMain.handle('check-system-requirements', async () => {
  return new Promise((resolve, reject) => {
    try {
      const scriptPath = getPythonScriptPath('lightweight_system_check.py');
      const pythonProcess = spawn(getPythonPath(), [scriptPath]);
      
      let data = '';
      const timeout = setTimeout(() => {
        pythonProcess.kill('SIGTERM');
        reject(new Error('System requirements check timeout'));
      }, 10 * 1000); // Back to 10 seconds since it's lightweight

      pythonProcess.stdout.on('data', (chunk) => {
        data += chunk;
      });

      pythonProcess.stderr.on('data', (data) => {
        console.error('System requirements check stderr:', data.toString());
      });

      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        try {
          if (code === 0 && data.trim()) {
            const result = JSON.parse(data);
            resolve(result);
          } else {
            reject(new Error('System requirements check failed'));
          }
        } catch (err) {
          console.error('Error parsing system requirements:', err);
          reject(err);
        }
      });

      pythonProcess.on('error', (err) => {
        clearTimeout(timeout);
        reject(new Error(`Failed to check system requirements: ${err.message}`));
      });
    } catch (error) {
      console.error('Error in check-system-requirements:', error);
      reject(error);
    }
  });
});

// IPC handler for starting fine-tuning
ipcMain.handle('start-fine-tuning', async (event, args) => {
  return new Promise((resolve, reject) => {
    try {
      const scriptPath = getPythonScriptPath('fine_tuning.py');
      const scriptDir = path.dirname(scriptPath);
      const pythonProcess = spawn(getPythonPath(), ['-c', `
import sys
import json
sys.path.append('${scriptDir.replace(/'/g, "\\'")}')
from fine_tuning import fine_tuning_manager

args = ${JSON.stringify(args)}
result = fine_tuning_manager.start_fine_tuning(
    base_model=args['baseModel'],
    model_name=args['modelName'],
    learning_rate=args['learningRate'],
    epochs=args['epochs'],
    batch_size=args['batchSize'],
    files=args['files']
)
print(json.dumps(result))
      `]);
      
      let data = '';
      const timeout = setTimeout(() => {
        pythonProcess.kill('SIGTERM');
        reject(new Error('Fine-tuning start timeout'));
      }, 30 * 1000);

      pythonProcess.stdout.on('data', (chunk) => {
        const output = chunk.toString();
        data += output;
        
        // Check for progress updates
        const lines = output.split('\n');
        for (const line of lines) {
          if (line.startsWith('PROGRESS_UPDATE: ')) {
            try {
              const progressData = JSON.parse(line.replace('PROGRESS_UPDATE: ', ''));
              mainWindow.webContents.send('fine-tuning-progress', progressData);
            } catch (e) {
              console.error('Error parsing progress update:', e);
            }
          }
        }
      });

      pythonProcess.stderr.on('data', (data) => {
        console.error('Fine-tuning start stderr:', data.toString());
      });

      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        try {
          if (code === 0 && data.trim()) {
            const result = JSON.parse(data);
            resolve(result);
          } else {
            reject(new Error('Fine-tuning start failed'));
          }
        } catch (err) {
          console.error('Error parsing fine-tuning result:', err);
          reject(err);
        }
      });

      pythonProcess.on('error', (err) => {
        clearTimeout(timeout);
        reject(new Error(`Failed to start fine-tuning: ${err.message}`));
      });
    } catch (error) {
      console.error('Error in start-fine-tuning:', error);
      reject(error);
    }
  });
});

// IPC handler for exporting fine-tuned model to Ollama
ipcMain.handle('export-fine-tuned-model', async (event, modelName) => {
  return new Promise((resolve, reject) => {
    try {
      const scriptPath = getPythonScriptPath('fine_tuning.py');
      const scriptDir = path.dirname(scriptPath);
      const pythonProcess = spawn(getPythonPath(), ['-c', `
import sys
import json
sys.path.append('${scriptDir.replace(/'/g, "\\'")}')
from fine_tuning import fine_tuning_manager

result = fine_tuning_manager.export_to_ollama("${modelName}")
print(json.dumps(result))
      `]);
      
      let data = '';
      const timeout = setTimeout(() => {
        pythonProcess.kill('SIGTERM');
        resolve({ success: false, error: 'Export timeout' });
      }, 60 * 1000); // 1 minute timeout

      pythonProcess.stdout.on('data', (chunk) => {
        data += chunk;
      });

      pythonProcess.stderr.on('data', (data) => {
        console.error('Export fine-tuned model stderr:', data.toString());
      });

      pythonProcess.on('close', (code) => {
        clearTimeout(timeout);
        try {
          if (code === 0 && data.trim()) {
            const result = JSON.parse(data);
            resolve(result);
          } else {
            resolve({ success: false, error: 'Export failed' });
          }
        } catch (err) {
          console.error('Error parsing export result:', err);
          resolve({ success: false, error: 'Failed to parse export result' });
        }
      });

      pythonProcess.on('error', (err) => {
        clearTimeout(timeout);
        resolve({ success: false, error: `Failed to start export: ${err.message}` });
      });
    } catch (error) {
      console.error('Error in export-fine-tuned-model:', error);
      resolve({ success: false, error: error.message });
    }
  });
}); 