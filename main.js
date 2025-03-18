const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

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
    let scriptArgs = ['-u', path.join(__dirname, 'runAI.py')];

    // Pass query and model arguments to the Python script.
    scriptArgs.push('--query', args.query);
    scriptArgs.push('--model', args.model);

    // If a file was uploaded, pass its path.
    if (args.filePath) {
      scriptArgs.push('--file', args.filePath);
    }

    // Spawn the Python process.
    const pythonProcess = spawn('python', scriptArgs);

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
    const scriptArgs = [
      '-u',
      path.join(__dirname, 'downloadModel.py'),
      '--model',
      modelName,
    ];
    const pythonProcess = spawn('python', scriptArgs);

    let fullResponse = '';

    pythonProcess.stdout.on('data', (data) => {
      fullResponse += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
      resolve(fullResponse);
    });
  });
});

// IPC handler for retrieving AI model options
ipcMain.handle('get-ai-options', async () => {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python', [path.join(__dirname, 'getAIOptions.py')]);
    let data = '';

    pythonProcess.stdout.on('data', (chunk) => {
      data += chunk;
    });

    pythonProcess.on('close', (code) => {
      try {
        const options = JSON.parse(data);
        if (options.length === 0) {
          reject(new Error('No AI models returned.'));
        } else {
          resolve(options);
        }
      } catch (err) {
        reject(err);
      }
    });

    pythonProcess.on('error', (err) => {
      reject(err);
    });
  });
});
