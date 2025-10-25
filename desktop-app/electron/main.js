const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const Store = require('electron-store');
const dataPaths = require('./data-paths');

// Enhanced logging function
function log(level, message, data = null) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
  
  console.log(logMessage);
  if (data) {
    console.log('Data:', JSON.stringify(data, null, 2));
  }
  
  // Also write to log file if possible
  try {
    const logDir = appDataPaths?.logs || path.join(__dirname, '../logs');
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    const logFile = path.join(logDir, 'electron-main.log');
    fs.appendFileSync(logFile, logMessage + '\n');
    if (data) {
      fs.appendFileSync(logFile, 'Data: ' + JSON.stringify(data, null, 2) + '\n');
    }
  } catch (err) {
    // Ignore log file errors
  }
}

const store = new Store();

let mainWindow;
let backendProcess = null;
let frontendProcess = null;
const isDev = !app.isPackaged;

const BACKEND_PORT = 8000;
let FRONTEND_PORT = 3000;

// Initialize data directories on app start
let appDataPaths;
try {
  log('info', 'Initializing data directories...');
  appDataPaths = dataPaths.initializeDataDirectories();
  log('info', 'Data directories initialized successfully', appDataPaths);
} catch (error) {
  log('error', 'Failed to initialize data directories', { error: error.message });
  console.error('Failed to initialize data directories:', error);
}

function createWindow() {
  log('info', 'Creating main window...');
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    icon: path.join(__dirname, '../resources/icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false // Allow microphone access
    },
    autoHideMenuBar: true,
    title: 'Windows-Use AI'
  });

  log('info', 'Main window created successfully');

  // Handle microphone permissions
  mainWindow.webContents.session.setPermissionRequestHandler((webContents, permission, callback) => {
    log('info', 'Permission requested', { permission });
    
    if (permission === 'media') {
      // Grant microphone permission for voice mode
      log('info', 'Granting microphone permission for voice mode');
      callback(true);
    } else if (permission === 'microphone') {
      // Grant microphone permission
      log('info', 'Granting microphone permission');
      callback(true);
    } else {
      // Deny other permissions
      log('info', 'Denying permission', { permission });
      callback(false);
    }
  });

  // Set media permissions
  mainWindow.webContents.session.setPermissionCheckHandler((webContents, permission, requestingOrigin, details) => {
    log('info', 'Permission check', { permission, requestingOrigin });
    
    if (permission === 'media' || permission === 'microphone') {
      log('info', 'Allowing media/microphone access');
      return true;
    }
    
    return false;
  });

  if (!store.get('termsAccepted')) {
    log('info', 'Terms not accepted, showing terms window');
    showTermsWindow();
  } else {
    log('info', 'Terms already accepted, starting application');
    startApplication();
  }

  mainWindow.on('closed', () => {
    log('info', 'Main window closed');
    mainWindow = null;
  });
}

// Handle microphone permission requests
ipcMain.handle('request-microphone-permission', async () => {
  log('info', 'Microphone permission requested via IPC');
  try {
    // Request microphone access
    const result = await mainWindow.webContents.executeJavaScript(`
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(() => {
          console.log('Microphone permission granted');
          return true;
        })
        .catch((error) => {
          console.error('Microphone permission denied:', error);
          return false;
        })
    `);
    
    log('info', 'Microphone permission result', { granted: result });
    return result;
  } catch (error) {
    log('error', 'Failed to request microphone permission', { error: error.message });
    return false;
  }
});

// Handle audio device enumeration
ipcMain.handle('get-audio-devices', async () => {
  log('info', 'Audio devices requested via IPC');
  try {
    const devices = await mainWindow.webContents.executeJavaScript(`
      navigator.mediaDevices.enumerateDevices()
        .then(devices => {
          return devices
            .filter(device => device.kind === 'audioinput' || device.kind === 'audiooutput')
            .map(device => ({
              deviceId: device.deviceId,
              label: device.label || \`\${device.kind} \${device.deviceId.slice(0, 8)}\`,
              kind: device.kind
            }));
        })
        .catch(() => [])
    `);
    
    log('info', 'Audio devices retrieved', { count: devices.length });
    return devices;
  } catch (error) {
    log('error', 'Failed to get audio devices', { error: error.message });
    return [];
  }
});

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
    log('info', 'Starting backend process...', { isDev, isPackaged: app.isPackaged });
    console.log(`isDev: ${isDev}, isPackaged: ${app.isPackaged}`);
    
    const backendPath = isDev
      ? path.join(__dirname, '../../api_server.py')
      : path.join(process.resourcesPath, 'backend', 'api_server.exe');

    const pythonCmd = isDev ? path.join(__dirname, '../../venv/Scripts/python.exe') : backendPath;
    const args = isDev ? [backendPath] : [];

    log('info', 'Backend command details', { pythonCmd, args, backendPath });
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

    log('info', 'Backend environment variables set', {
      WINDOWS_USE_DATA_PATH: appDataPaths.data,
      WINDOWS_USE_LOGS_PATH: appDataPaths.logs,
      WINDOWS_USE_CONFIG_PATH: appDataPaths.config,
      WINDOWS_USE_CACHE_PATH: appDataPaths.cache
    });

    // Load .env file from config directory if it exists
    const envFilePath = dataPaths.getEnvFilePath();
    if (fs.existsSync(envFilePath)) {
      log('info', 'Loading .env file', { envFilePath });
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
      log('info', 'Environment variables loaded from .env file');
    } else {
      log('info', 'No .env file found, using system environment variables');
    }

    log('info', 'Spawning backend process...', { cwd: isDev ? path.join(__dirname, '../..') : path.join(process.resourcesPath, 'backend') });
    backendProcess = spawn(pythonCmd, args, {
      cwd: isDev ? path.join(__dirname, '../..') : path.join(process.resourcesPath, 'backend'),
      env: backendEnv
    });

    log('info', 'Backend process spawned successfully', { pid: backendProcess.pid });

    backendProcess.stdout.on('data', (data) => {
      const output = data.toString();
      log('info', 'Backend stdout', { output: output.trim() });
      console.log(`Backend: ${data}`);
      
      // Enhanced startup detection
      if (output.includes('Uvicorn running') || output.includes('Application startup complete')) {
        log('info', 'Backend startup detected, resolving promise');
        resolve();
      }
      
      // Log specific error patterns
      if (output.includes('Google API key is not set')) {
        log('error', 'Backend API key error detected', { output: output.trim() });
        console.log('🚨 BACKEND ERROR: Google API key is not set!');
      }
      
      if (output.includes('Failed to initialize agent')) {
        log('error', 'Backend agent initialization failed', { output: output.trim() });
        console.log('🚨 BACKEND ERROR: Agent initialization failed!');
      }
    });

    backendProcess.stderr.on('data', (data) => {
      const error = data.toString();
      log('error', 'Backend stderr', { error: error.trim() });
      console.error(`Backend Error: ${data}`);
    });

    backendProcess.on('error', (error) => {
      log('error', 'Backend process error', { error: error.message });
      console.error('Failed to start backend:', error);
      reject(error);
    });

    backendProcess.on('exit', (code) => {
      log('warn', 'Backend process exited', { code });
      console.log(`Backend process exited with code ${code}`);
      if (code !== 0 && code !== null) {
        log('error', 'Backend process exited with non-zero code', { code });
        reject(new Error(`Backend exited with code ${code}`));
      }
    });

    log('info', 'Setting 8-second timeout for backend startup');
    setTimeout(() => {
      log('info', 'Backend startup timeout reached, resolving anyway');
      resolve();
    }, 8000);
  });
}

function startFrontend() {
  return new Promise((resolve) => {
    log('info', 'Starting frontend process...', { isDev });
    
    if (isDev) {
      const frontendPath = path.join(__dirname, '../../frontend');
      log('info', 'Starting development frontend', { frontendPath });
      frontendProcess = spawn('npm.cmd', ['run', 'dev'], {
        cwd: frontendPath,
        shell: true
      });

      frontendProcess.stdout.on('data', (data) => {
        const output = data.toString();
        log('info', 'Frontend stdout', { output: output.trim() });
        console.log(`Frontend: ${data}`);
        
        // Parse the actual port from Next.js output
        const portMatch = output.match(/Local:\s+http:\/\/localhost:(\d+)/);
        if (portMatch) {
          FRONTEND_PORT = parseInt(portMatch[1]);
          log('info', 'Frontend port detected', { port: FRONTEND_PORT });
        }
        
        if (output.includes('Ready') || output.includes('compiled')) {
          log('info', 'Frontend ready detected, resolving promise');
          resolve();
        }
      });

      frontendProcess.stderr.on('data', (data) => {
        const error = data.toString();
        log('error', 'Frontend stderr', { error: error.trim() });
        console.error(`Frontend: ${data}`);
      });

      log('info', 'Setting 10-second timeout for frontend startup');
      setTimeout(() => {
        log('info', 'Frontend startup timeout reached, resolving anyway');
        resolve();
      }, 10000);
    } else {
      const frontendPath = path.join(process.resourcesPath, 'frontend-build');
      log('info', 'Starting production frontend', { frontendPath });
      frontendProcess = spawn('npx.cmd', ['serve', '-s', '.', '-l', FRONTEND_PORT], {
        cwd: frontendPath,
        shell: true
      });

      frontendProcess.stdout.on('data', (data) => {
        const output = data.toString();
        log('info', 'Frontend stdout', { output: output.trim() });
        console.log(`Frontend: ${data}`);
      });

      log('info', 'Setting 3-second timeout for production frontend');
      setTimeout(() => {
        log('info', 'Production frontend timeout reached, resolving');
        resolve();
      }, 3000);
    }
  });
}

async function startApplication() {
  try {
    log('info', 'Starting application initialization...');
    mainWindow.webContents.send('status', 'Starting backend server...');
    log('info', 'Starting backend server...');
    await startBackend();
    log('info', 'Backend server started successfully');

    mainWindow.webContents.send('status', 'Starting frontend...');
    log('info', 'Starting frontend...');
    await startFrontend();
    log('info', 'Frontend started successfully');

    mainWindow.webContents.send('status', 'Loading application...');
    log('info', 'Loading application...');
    
    setTimeout(() => {
      const url = `http://localhost:${FRONTEND_PORT}`;
      log('info', 'Loading application URL', { url });
      mainWindow.loadURL(url);
    }, 2000);

  } catch (error) {
    log('error', 'Failed to start application', { error: error.message, stack: error.stack });
    console.error('Failed to start application:', error);
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start the application: ${error.message}\n\nPlease check that all dependencies are installed.`
    );
    app.quit();
  }
}

function stopProcesses() {
  log('info', 'Stopping processes...');
  
  if (backendProcess) {
    log('info', 'Stopping backend process...', { pid: backendProcess.pid });
    console.log('Stopping backend process...');
    backendProcess.kill();
    backendProcess = null;
  }
  
  if (frontendProcess) {
    log('info', 'Stopping frontend process...', { pid: frontendProcess.pid });
    console.log('Stopping frontend process...');
    frontendProcess.kill();
    frontendProcess = null;
  }
  
  log('info', 'All processes stopped');
}

// Set command line arguments for microphone access
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
app.commandLine.appendSwitch('disable-features', 'VizDisplayCompositor');

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

