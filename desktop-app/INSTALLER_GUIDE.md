# Installer Guide for Windows-Use AI Desktop App

This guide explains how the installer works and where app data is stored.

## Installer Features

The Windows-Use AI installer creates a professional NSIS-based installation package with the following features:

### Installation Directories

1. **Application Installation** (User selectable, default: `C:\Program Files\Windows-Use AI`)
   - Contains the application executable and resources
   - Read-only for normal users

2. **Application Data** (Automatic: `C:\ProgramData\WindowsUse`)
   - Shared data accessible to all users
   - Writable by all users (installer sets appropriate permissions)
   - Contains:
     - `logs/` - Application logs
     - `config/` - Configuration files (including .env)
     - `cache/` - Temporary cache files
     - `data/` - General application data

3. **User Data** (Automatic: `%APPDATA%\WindowsUse`)
   - User-specific data
   - Contains:
     - `logs/` - User-specific logs
     - `config/` - User preferences

### What the Installer Does

1. **Creates Directory Structure**
   ```
   C:\ProgramData\WindowsUse\
   ├── logs\
   ├── config\
   │   └── .env (created with template)
   ├── cache\
   └── data\
   
   %APPDATA%\WindowsUse\
   ├── logs\
   └── config\
   ```

2. **Sets Permissions**
   - Grants all users read/write access to `C:\ProgramData\WindowsUse`
   - This allows the app to work without admin privileges after installation

3. **Creates Configuration Template**
   - Creates `.env` file at `C:\ProgramData\WindowsUse\config\.env`
   - Contains template for API keys and settings

4. **Registry Entries**
   - Stores data paths in registry for easy access
   - `HKLM\Software\WindowsUse\DataPath`
   - `HKCU\Software\WindowsUse\UserDataPath`

### Installation Options

- **Installation Directory**: User can choose where to install the app
- **Desktop Shortcut**: Creates shortcut on desktop
- **Start Menu**: Creates start menu entry
- **License Agreement**: Users must accept before installation

### Uninstallation

When uninstalling, users are given the option to:
- **Remove all data**: Deletes everything including logs and configuration
- **Keep data**: Preserves data at `C:\ProgramData\WindowsUse` for future reinstallation

## Building the Installer

### Prerequisites

1. Node.js and npm installed
2. Python installed (for backend build)
3. All dependencies installed:
   ```bash
   cd desktop-app
   npm install
   ```

### Build Steps

1. **Build Backend**
   ```bash
   npm run build:backend
   ```
   This creates `backend/api_server.exe`

2. **Build Frontend**
   ```bash
   npm run build:frontend
   ```
   This creates static frontend files in `frontend-build/`

3. **Build Installer**
   ```bash
   npm run electron:build
   ```
   This creates the installer in `dist/`

4. **Build Everything**
   ```bash
   npm run build:all
   ```
   Runs all build steps in sequence

### Output Files

After building, you'll find in `dist/`:

- `Windows-Use AI Setup X.X.X.exe` - NSIS installer (recommended)
- `Windows-Use AI X.X.X.exe` - Portable version (no installation needed)
- `win-unpacked/` - Unpacked application files

## Using the App with Data Directories

### Configuration

The app loads configuration from `C:\ProgramData\WindowsUse\config\.env`

To configure API keys:
1. Open the config folder (can be done from app settings)
2. Edit `.env` file
3. Restart the app

Example `.env`:
```env
GOOGLE_API_KEY=your_api_key_here
ELEVENLABS_API_KEY=your_api_key_here
DEEPGRAM_API_KEY=your_api_key_here

ENABLE_TTS=true
TTS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

### Logs

Logs are stored at:
- Shared: `C:\ProgramData\WindowsUse\logs\`
- User: `%APPDATA%\WindowsUse\logs\`

### Accessing Data Folders

From within the app (once frontend is updated):
- Settings → Open Data Folder
- Settings → Open Config Folder
- Settings → Open Logs Folder

## Troubleshooting

### Permission Issues

If the app can't write to `C:\ProgramData\WindowsUse`:
1. The app will automatically fall back to `%APPDATA%\WindowsUse`
2. Check folder permissions:
   ```cmd
   icacls "C:\ProgramData\WindowsUse"
   ```

### Missing Directories

If directories aren't created during installation:
1. Run the app once - it will create them automatically
2. The app initializes directories on first launch

### Environment Variables

The app sets these environment variables for the backend:
- `WINDOWS_USE_DATA_PATH` - Main data directory
- `WINDOWS_USE_LOGS_PATH` - Logs directory
- `WINDOWS_USE_CONFIG_PATH` - Config directory
- `WINDOWS_USE_CACHE_PATH` - Cache directory

## Development vs Production

### Development Mode (npm run electron:dev)
- Uses project root directories
- Loads .env from project root
- Hot reloading enabled

### Production Mode (installed app)
- Uses `C:\ProgramData\WindowsUse`
- Loads .env from config directory
- Optimized performance

## Security Considerations

1. **API Keys**: Stored in `.env` file, not exposed to other users
2. **Permissions**: Only necessary permissions granted
3. **Data Isolation**: User data separated from shared data
4. **No Admin Required**: App runs with normal user privileges after installation

## Best Practices

1. **Backup Configuration**: Before uninstalling, backup `C:\ProgramData\WindowsUse\config\.env`
2. **Log Rotation**: Periodically clean old logs from `logs/` directories
3. **Updates**: When updating, configuration is preserved
4. **Multiple Users**: Each user can have their own preferences in `%APPDATA%`

## Technical Details

### Installer Script

The installer uses a custom NSIS script (`installer-script.nsh`) that:
- Creates directory structure with proper permissions
- Handles both install and uninstall scenarios
- Provides user choices during uninstallation

### Data Path Resolution

The app uses this priority for data paths:
1. Try `C:\ProgramData\WindowsUse` (shared)
2. Fall back to `%APPDATA%\WindowsUse` (user-specific)
3. Always accessible, no admin needed after installation

### Environment Loading

The Electron app:
1. Initializes data directories on startup
2. Loads `.env` from config directory
3. Passes environment to backend process
4. Backend uses environment variables to find data

