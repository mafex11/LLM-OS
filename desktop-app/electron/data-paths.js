/**
 * Data path management for Windows-Use AI
 * Handles both ProgramData (shared) and AppData (user-specific) directories
 */

const path = require('path');
const fs = require('fs');
const os = require('os');

/**
 * Get the main data directory path
 * Tries ProgramData first, falls back to AppData if not accessible
 */
function getDataPath() {
  // On Windows, prefer C:\ProgramData\WindowsUse
  const programDataPath = path.join(process.env.PROGRAMDATA || 'C:\\ProgramData', 'WindowsUse');
  
  // Check if ProgramData directory exists and is writable
  try {
    if (!fs.existsSync(programDataPath)) {
      fs.mkdirSync(programDataPath, { recursive: true });
    }
    
    // Test write access
    const testFile = path.join(programDataPath, '.write-test');
    fs.writeFileSync(testFile, 'test');
    fs.unlinkSync(testFile);
    
    return programDataPath;
  } catch (err) {
    console.warn('Cannot write to ProgramData, using AppData instead:', err.message);
    
    // Fall back to user's AppData\Roaming
    const appDataPath = path.join(
      process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming'),
      'WindowsUse'
    );
    
    if (!fs.existsSync(appDataPath)) {
      fs.mkdirSync(appDataPath, { recursive: true });
    }
    
    return appDataPath;
  }
}

/**
 * Get the user-specific data directory path
 */
function getUserDataPath() {
  const appDataPath = path.join(
    process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming'),
    'WindowsUse'
  );
  
  if (!fs.existsSync(appDataPath)) {
    fs.mkdirSync(appDataPath, { recursive: true });
  }
  
  return appDataPath;
}

/**
 * Get specific subdirectory paths
 */
function getLogsPath() {
  const logsPath = path.join(getDataPath(), 'logs');
  if (!fs.existsSync(logsPath)) {
    fs.mkdirSync(logsPath, { recursive: true });
  }
  return logsPath;
}

function getConfigPath() {
  const configPath = path.join(getDataPath(), 'config');
  if (!fs.existsSync(configPath)) {
    fs.mkdirSync(configPath, { recursive: true });
  }
  return configPath;
}

function getCachePath() {
  const cachePath = path.join(getDataPath(), 'cache');
  if (!fs.existsSync(cachePath)) {
    fs.mkdirSync(cachePath, { recursive: true });
  }
  return cachePath;
}

function getAppDataPath() {
  const dataPath = path.join(getDataPath(), 'data');
  if (!fs.existsSync(dataPath)) {
    fs.mkdirSync(dataPath, { recursive: true });
  }
  return dataPath;
}

/**
 * Get the .env file path
 */
function getEnvFilePath() {
  return path.join(getConfigPath(), '.env');
}

/**
 * Initialize all data directories
 */
function initializeDataDirectories() {
  const paths = {
    data: getDataPath(),
    userData: getUserDataPath(),
    logs: getLogsPath(),
    config: getConfigPath(),
    cache: getCachePath(),
    appData: getAppDataPath(),
    envFile: getEnvFilePath()
  };
  
  console.log('Data directories initialized:');
  Object.entries(paths).forEach(([key, value]) => {
    console.log(`  ${key}: ${value}`);
  });
  
  // Create .env template if it doesn't exist
  if (!fs.existsSync(paths.envFile)) {
    const envTemplate = `# Windows-Use AI Configuration
# Add your API keys here

GOOGLE_API_KEY=
ELEVENLABS_API_KEY=
DEEPGRAM_API_KEY=

# TTS Settings
ENABLE_TTS=true
TTS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
`;
    fs.writeFileSync(paths.envFile, envTemplate);
    console.log('Created .env template at:', paths.envFile);
  }
  
  return paths;
}

module.exports = {
  getDataPath,
  getUserDataPath,
  getLogsPath,
  getConfigPath,
  getCachePath,
  getAppDataPath,
  getEnvFilePath,
  initializeDataDirectories
};

