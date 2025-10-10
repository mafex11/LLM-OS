# Build Windows Installer - Quick Start

This guide will walk you through building the Windows installer for Windows-Use AI.

## Prerequisites

Before you start, make sure you have:

- ✅ **Node.js** (v18 or later) - [Download here](https://nodejs.org/)
- ✅ **Python** (v3.10 or later) - [Download here](https://www.python.org/)
- ✅ **Git** (optional, for cloning) - [Download here](https://git-scm.com/)

## Quick Build (One Command)

```bash
cd desktop-app
npm install
npm run build:all
```

This will:
1. Build the Python backend into a standalone .exe
2. Build the Next.js frontend into static files
3. Package everything into a Windows installer

**Output**: `dist/Windows-Use AI Setup 1.0.0.exe`

## Step-by-Step Build

If you prefer to build each component separately:

### 1. Install Dependencies

```bash
cd desktop-app
npm install
```

### 2. Build Backend

```bash
npm run build:backend
```

This uses PyInstaller to create `backend/api_server.exe` from the Python code.

### 3. Build Frontend

```bash
npm run build:frontend
```

This builds the Next.js app into static files in `frontend-build/`.

### 4. Build Installer

```bash
npm run electron:build
```

This uses electron-builder to create the NSIS installer.

## Output Files

After building, check the `dist/` folder:

```
dist/
├── Windows-Use AI Setup 1.0.0.exe    ← Main installer (recommended)
├── Windows-Use AI 1.0.0.exe          ← Portable version
├── win-unpacked/                     ← Unpacked files (for testing)
└── builder-*.yml                     ← Build metadata
```

### Which File to Distribute?

- **`Windows-Use AI Setup 1.0.0.exe`** - Full installer with automatic directory setup (recommended for users)
- **`Windows-Use AI 1.0.0.exe`** - Portable version, no installation needed

## Testing the Installer

### Test on Current Machine

1. Navigate to `dist/`
2. Run `Windows-Use AI Setup 1.0.0.exe`
3. Follow installation wizard
4. Check that these folders were created:
   - `C:\ProgramData\WindowsUse\`
   - `%APPDATA%\WindowsUse\`
5. Launch the app from desktop shortcut
6. Verify app works correctly

### Test Configuration

1. Navigate to `C:\ProgramData\WindowsUse\config\`
2. Open `.env` file
3. Add your API keys:
   ```
   GOOGLE_API_KEY=your_key_here
   ELEVENLABS_API_KEY=your_key_here
   DEEPGRAM_API_KEY=your_key_here
   ```
4. Restart the app
5. Verify API keys are loaded

### Test Uninstaller

1. Go to Settings → Apps & Features
2. Find "Windows-Use AI"
3. Click Uninstall
4. You'll be asked: "Keep data or remove?"
5. Test both options

## Troubleshooting

### Build Fails - Backend

**Error**: `PyInstaller not found`

**Solution**:
```bash
cd ..
pip install pyinstaller
cd desktop-app
npm run build:backend
```

### Build Fails - Frontend

**Error**: `Next.js build failed`

**Solution**:
```bash
cd ../frontend
npm install
npm run build
cd ../desktop-app
```

### Build Fails - Installer

**Error**: `electron-builder not found`

**Solution**:
```bash
npm install
npm run electron:build
```

### Installer Doesn't Create Folders

**Check**:
1. The `installer-script.nsh` file exists in `desktop-app/`
2. The package.json has `"include": "installer-script.nsh"` in NSIS config
3. Run installer as Administrator

### App Can't Write to ProgramData

**Solution**: The app automatically falls back to `%APPDATA%` if it can't write to ProgramData.

To fix permissions manually:
```cmd
icacls "C:\ProgramData\WindowsUse" /grant Users:F /t
```

## Advanced Options

### Custom Icon

Replace `resources/icon.ico` with your custom icon (256x256 recommended).

### Custom License

Edit `resources/LICENSE.txt` with your license text.

### Change App Name/Version

Edit `desktop-app/package.json`:
```json
{
  "name": "windows-use-desktop",
  "version": "1.0.0",
  "build": {
    "productName": "Windows-Use AI"
  }
}
```

### Build for Testing (Faster)

For development/testing, build only unpacked version:
```bash
npm run electron:build -- --dir
```

Output: `dist/win-unpacked/Windows-Use AI.exe` (no installer)

### Enable Code Signing

To sign your installer (requires code signing certificate):

1. Get a code signing certificate
2. Edit `package.json`:
   ```json
   "win": {
     "sign": "./sign.js",
     "certificateFile": "path/to/cert.pfx",
     "certificatePassword": "password"
   }
   ```

## Distribution

### For End Users

Distribute: `Windows-Use AI Setup 1.0.0.exe`

**Installation Instructions for Users**:
1. Download the installer
2. Run as Administrator (one time only)
3. Follow installation wizard
4. Launch from desktop shortcut
5. Configure API keys in Settings
6. Start using the app

### For Portable Use

Distribute: `Windows-Use AI 1.0.0.exe`

**Usage Instructions**:
1. Download the portable version
2. Extract to any folder
3. Run `Windows-Use AI.exe`
4. App creates data folders in `%APPDATA%\WindowsUse`

## File Size Optimization

The installer will be large (~200-400MB) due to:
- Electron framework (~150MB)
- Python runtime (~50MB)
- Dependencies (~50-100MB)

To reduce size:
- Remove unused Python packages before building backend
- Enable compression in electron-builder config
- Use portable version (slightly smaller)

## Continuous Integration

To automate builds with GitHub Actions, create `.github/workflows/build.yml`:

```yaml
name: Build Installer

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        cd desktop-app
        npm install
    
    - name: Build installer
      run: |
        cd desktop-app
        npm run build:all
    
    - name: Upload artifact
      uses: actions/upload-artifact@v2
      with:
        name: windows-installer
        path: desktop-app/dist/*.exe
```

## Support

If you encounter issues:

1. Check `desktop-app/dist/` for build logs
2. Check `app.log` after running the app
3. Check `C:\ProgramData\WindowsUse\logs\` for runtime logs
4. Review `INSTALLER_GUIDE.md` for detailed documentation

## Next Steps

After building:

1. ✅ Test the installer on a clean Windows machine
2. ✅ Verify all features work correctly
3. ✅ Test API key configuration
4. ✅ Test uninstaller
5. ✅ Distribute to users

**Ready to distribute!** 🎉

