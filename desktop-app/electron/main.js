const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const Store = require('electron-store');
const dataPaths = require('./data-paths');

const store = new Store();

let mainWindow;
let backendProcess = null;
let frontendProcess = null;
const isDev = !app.isPackaged;

const BACKEND_PORT = 8000;
const FRONTEND_PORT = 3000;

// Initialize data directories on app start
let appDataPaths;
try {
  appDataPaths = dataPaths.initializeDataDirectories();
} catch (error) {
  console.error('Failed to initialize data directories:', error);
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    icon: path.join(__dirname, '../resources/icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    autoHideMenuBar: true,
    title: 'Windows-Use AI'
  });

  if (!store.get('termsAccepted')) {
    showTermsWindow();
  } else {
    startApplication();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function showTermsWindow() {
  const termsWindow = new BrowserWindow({
    width: 800,
    height: 600,
    parent: mainWindow,
    modal: true,
    resizable: false,
    icon: path.join(__dirname, '../resources/icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    autoHideMenuBar: true,
    title: 'Terms and Conditions'
  });

  termsWindow.loadFile(path.join(__dirname, 'terms.html'));

  ipcMain.once('accept-terms', () => {
    store.set('termsAccepted', true);
    termsWindow.close();
    startApplication();
  });

  ipcMain.once('decline-terms', () => {
    termsWindow.close();
    app.quit();
  });

  termsWindow.on('closed', () => {
    if (!store.get('termsAccepted')) {
      app.quit();
    }
  });
}

function startBackend() {
  return new Promise((resolve, reject) => {
    console.log(`isDev: ${isDev}, isPackaged: ${app.isPackaged}`);
    
    const backendPath = isDev
      ? path.join(__dirname, '../../api_server.py')
      : path.join(process.resourcesPath, 'backend', 'api_server.exe');

    const pythonCmd = isDev ? 'python' : backendPath;
    const args = isDev ? [backendPath] : [];

    console.log(`Starting backend: ${pythonCmd}`, args);
    console.log(`Backend path: ${backendPath}`);

    // Set environment variables for data paths
    const backendEnv = {
      ...process.env,
      WINDOWS_USE_DATA_PATH: appDataPaths.data,
      WINDOWS_USE_LOGS_PATH: appDataPaths.logs,
      WINDOWS_USE_CONFIG_PATH: appDataPaths.config,
      WINDOWS_USE_CACHE_PATH: appDataPaths.cache
    };

    // Load .env file from config directory if it exists
    const envFilePath = dataPaths.getEnvFilePath();
    if (fs.existsSync(envFilePath)) {
      console.log('Loading .env from:', envFilePath);
      const envContent = fs.readFileSync(envFilePath, 'utf-8');
      envContent.split('\n').forEach(line => {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
          const [key, ...valueParts] = trimmed.split('=');
          const value = valueParts.join('=').trim();
          if (value) {
            backendEnv[key.trim()] = value;
          }
        }
      });
    }

    backendProcess = spawn(pythonCmd, args, {
      cwd: isDev ? path.join(__dirname, '../..') : path.join(process.resourcesPath, 'backend'),
      env: backendEnv
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
      if (data.toString().includes('Uvicorn running') || data.toString().includes('Application startup complete')) {
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`Backend Error: ${data}`);
    });

    backendProcess.on('error', (error) => {
      console.error('Failed to start backend:', error);
      reject(error);
    });

    backendProcess.on('exit', (code) => {
      console.log(`Backend process exited with code ${code}`);
      if (code !== 0 && code !== null) {
        reject(new Error(`Backend exited with code ${code}`));
      }
    });

    setTimeout(resolve, 8000);
  });
}

function startFrontend() {
  return new Promise((resolve) => {
    if (isDev) {
      const frontendPath = path.join(__dirname, '../../frontend');
      frontendProcess = spawn('npm.cmd', ['run', 'dev'], {
        cwd: frontendPath,
        shell: true
      });

      frontendProcess.stdout.on('data', (data) => {
        console.log(`Frontend: ${data}`);
        if (data.toString().includes('Ready') || data.toString().includes('compiled')) {
          resolve();
        }
      });

      frontendProcess.stderr.on('data', (data) => {
        console.error(`Frontend: ${data}`);
      });

      setTimeout(resolve, 10000);
    } else {
      const frontendPath = path.join(process.resourcesPath, 'frontend-build');
      frontendProcess = spawn('npx.cmd', ['serve', '-s', '.', '-l', FRONTEND_PORT], {
        cwd: frontendPath,
        shell: true
      });

      frontendProcess.stdout.on('data', (data) => {
        console.log(`Frontend: ${data}`);
      });

      setTimeout(resolve, 3000);
    }
  });
}

async function startApplication() {
  try {
    mainWindow.webContents.send('status', 'Starting backend server...');
    await startBackend();

    mainWindow.webContents.send('status', 'Starting frontend...');
    await startFrontend();

    mainWindow.webContents.send('status', 'Loading application...');
    
    setTimeout(() => {
      mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`);
    }, 2000);

  } catch (error) {
    console.error('Failed to start application:', error);
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start the application: ${error.message}\n\nPlease check that all dependencies are installed.`
    );
    app.quit();
  }
}

function stopProcesses() {
  if (backendProcess) {
    console.log('Stopping backend process...');
    backendProcess.kill();
    backendProcess = null;
  }
  
  if (frontendProcess) {
    console.log('Stopping frontend process...');
    frontendProcess.kill();
    frontendProcess = null;
  }
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
  stopProcesses();
  app.quit();
});

app.on('before-quit', () => {
  stopProcesses();
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

ipcMain.handle('open-external', async (event, url) => {
  await shell.openExternal(url);
});

ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('get-data-paths', () => {
  return appDataPaths;
});

ipcMain.handle('open-data-folder', async () => {
  await shell.openPath(appDataPaths.data);
});

ipcMain.handle('open-config-folder', async () => {
  await shell.openPath(appDataPaths.config);
});

ipcMain.handle('open-logs-folder', async () => {
  await shell.openPath(appDataPaths.logs);
});

