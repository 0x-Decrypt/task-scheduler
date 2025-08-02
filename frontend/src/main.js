const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    icon: path.join(__dirname, '../assets/icon.png')
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  const pythonPath = process.platform === 'win32' ? 
    path.join(__dirname, '../../.venv/Scripts/python.exe') :
    path.join(__dirname, '../../.venv/bin/python');
  
  const backendScript = path.join(__dirname, '../../backend/simple_api.py');
  
  backendProcess = spawn(pythonPath, [backendScript], {
    cwd: path.join(__dirname, '../../backend'),
    stdio: 'inherit'
  });

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend:', err);
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

app.whenReady().then(() => {
  // Only start backend if not in development mode (backend likely already running)
  if (!process.argv.includes('--dev')) {
    startBackend();
    // Wait a bit for backend to start
    setTimeout(() => {
      createWindow();
    }, 2000);
  } else {
    // In dev mode, assume backend is already running
    createWindow();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});
