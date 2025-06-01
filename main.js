const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Helper function to get the correct path for Python scripts
function getPythonScriptPath(scriptName) {
  if (app.isPackaged) {
    // In production, scripts are in the resources directory
    return path.join(process.resourcesPath, scriptName);
  } else {
    // In development, scripts are in the project root
    return path.join(__dirname, scriptName);
  }
}

// Helper function to get Python executable path
function getPythonPath() {
  if (process.platform === 'win32') {
    return 'python';  // Windows will use the system Python
  } else {
    return 'python3'; // Unix-like systems typically use python3
  }
}

// Helper function to get the path for theMessages.txt
function getMessagesFilePath() {
  if (app.isPackaged) {
    // In production, use the resources directory
    return path.join(process.resourcesPath, 'theMessages.txt');
  } else {
    // In development, use the project root
    return path.join(__dirname, 'theMessages.txt');
  }
}

// Ensure theMessages.txt exists in the correct location
function ensureMessagesFileExists() {
  const messagesPath = getMessagesFilePath();
  if (!fs.existsSync(messagesPath)) {
    fs.writeFileSync(messagesPath, '');
  }
}

// Create the application window
function createWindow() {
  const win = new BrowserWindow({
    width: 960,
    height: 885,
    backgroundColor: '#0D4D66',  // Match your dark background
    autoHideMenuBar: true,       // Hide the menu bar by default
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // Remove the default application menu completely
  Menu.setApplicationMenu(null);

  // Load your index.html file
  win.loadFile('index.html');
}

app.whenReady().then(() => {
  // Ensure theMessages.txt exists when the app starts
  ensureMessagesFileExists();
  createWindow();

  // Re-create window on macOS when dock icon is clicked.
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
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
      { name: 'PDF or Image', extensions: ['pdf', 'png', 'jpg', 'jpeg', 'bmp', 'gif'] },
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
  // args: { query: string, model: string, filePath?: string }
  return new Promise((resolve, reject) => {
    const scriptPath = getPythonScriptPath('runAI.py');
    console.log('Python script path:', scriptPath);
    
    let scriptArgs = ['-u', scriptPath];

    // Pass query and model arguments to the Python script.
    scriptArgs.push('--query', args.query);
    scriptArgs.push('--model', args.model);

    // If a file was uploaded, pass its path.
    if (args.filePath) {
      scriptArgs.push('--file', args.filePath);
    }

    // Spawn the Python process.
    const pythonProcess = spawn(getPythonPath(), scriptArgs);

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
      resolve(fullResponse);
    });
  });
});

// IPC handler for downloading a model
ipcMain.handle('download-model', async (event, modelName) => {
  return new Promise((resolve, reject) => {
    const scriptPath = getPythonScriptPath('downloadModel.py');
    console.log('Python script path:', scriptPath);
    
    const scriptArgs = [
      '-u',
      scriptPath,
      '--model',
      modelName,
    ];
    const pythonProcess = spawn(getPythonPath(), scriptArgs);

    pythonProcess.stdout.on('data', (data) => {
      data.toString().split('\n').forEach(line => {
        if (line.trim()) {
          try {
            const progress = JSON.parse(line);
            // Send progress to renderer
            event.sender.send('download-progress', progress);
            if (progress.progress === 100 || progress.status === "Cannot be installed") {
              resolve(progress);
            }
          } catch (e) {}
        }
      });
    });

    pythonProcess.stderr.on('data', (data) => {
      reject(new Error(data.toString()));
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Process exited with code ${code}`));
      }
    });
  });
});

// IPC handler for retrieving AI model options
ipcMain.handle('get-ai-options', async () => {
  return new Promise((resolve, reject) => {
    const scriptPath = getPythonScriptPath('getAIOptions.py');
    console.log('Python script path:', scriptPath);
    
    const pythonProcess = spawn(getPythonPath(), [scriptPath]);
    let data = '';

    pythonProcess.stdout.on('data', (chunk) => {
      data += chunk;
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
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
      console.error('Error spawning Python process:', err);
      // Return "No models found" on error
      resolve(["No models found"]);
    });
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
