# 🖥️ Desktop Application Build Guide

This guide explains how to build and distribute Windows-Use as a standalone desktop application.

## 📋 Overview

The desktop application packages the entire Windows-Use system into a single installer that users can download and run without any technical setup. It includes:

- **Electron Wrapper**: Modern desktop app framework
- **Python Backend**: Packaged as standalone executable (no Python installation needed)
- **Next.js Frontend**: Pre-built and bundled
- **Terms & Conditions**: Professional onboarding flow
- **Branding**: Custom logo and app icon
- **Installer**: NSIS-based Windows installer

## 🎯 Quick Start

### Build the Desktop App

1. Run the automated build script:
   ```bash
   build.bat
   ```

2. Find your installer in:
   ```
   desktop-app/dist/Windows-Use AI Setup 1.0.0.exe
   ```

3. Distribute the installer to users!

## 🏗️ Architecture

```
Desktop App
├── Electron Main Process
│   ├── Launches Python backend (api_server.exe)
│   ├── Launches Next.js frontend server
│   └── Manages application lifecycle
│
├── Python Backend (Bundled Executable)
│   ├── FastAPI server
│   ├── Windows-Use agent
│   └── All dependencies included
│
├── Next.js Frontend (Pre-built)
│   ├── React UI
│   ├── Static assets
│   └── API client
│
└── Resources
    ├── App icon
    ├── Terms & Conditions
    └── License
```

## 📦 What Gets Built

### 1. Backend Executable (`api_server.exe`)

PyInstaller bundles the entire Python backend into a single executable:
- FastAPI server
- Windows-Use agent
- All Python dependencies
- LangChain and Google AI libraries

**Size**: ~300-500 MB (includes Python runtime and all dependencies)

### 2. Frontend Build

Next.js exports a static build:
- Optimized React components
- CSS and JavaScript bundles
- Static assets

**Size**: ~50-100 MB

### 3. Electron App

Electron provides the desktop wrapper:
- Window management
- System integration
- Auto-updates (configurable)
- Process management

**Size**: ~150-200 MB (includes Chromium and Node.js)

### 4. Installer

NSIS creates a professional Windows installer:
- One-click installation
- Terms acceptance
- Desktop shortcuts
- Uninstaller

**Total Size**: ~500-800 MB

## 🎨 Customization

### Change App Name and Branding

Edit `desktop-app/package.json`:

```json
{
  "name": "your-app-name",
  "version": "1.0.0",
  "build": {
    "productName": "Your App Name",
    "appId": "com.yourcompany.appname"
  }
}
```

### Add Custom Logo

1. Create a 256x256 PNG logo
2. Convert to .ico format (use https://convertico.com/)
3. Replace `desktop-app/resources/icon.ico`

### Customize Terms & Conditions

Edit `desktop-app/electron/terms.html` with your custom terms.

### Modify UI Branding

Update the frontend in `frontend/src/` with your branding:
- Colors in `frontend/tailwind.config.ts`
- Logo in `frontend/public/`
- App name in `frontend/src/app/layout.tsx`

## 🚀 Distribution

### For End Users

Users download the installer and run it:

1. **Download**: `Windows-Use AI Setup 1.0.0.exe`
2. **Run Installer**: Follow installation wizard
3. **Accept Terms**: Read and accept terms & conditions
4. **Configure**: Add Google API key in settings
5. **Use**: Start automating Windows tasks!

### Installation Locations

- **Program Files**: `C:\Program Files\Windows-Use AI\`
- **User Data**: `%APPDATA%\windows-use-desktop\`
- **Shortcuts**: Desktop + Start Menu

### First-Time Setup

After installation, users need to:

1. Create a `.env` file in the installation directory:
   ```
   C:\Program Files\Windows-Use AI\resources\app\.env
   ```

2. Add their API key:
   ```env
   GOOGLE_API_KEY=your_key_here
   ENABLE_TTS=true
   ```

3. Restart the application

**Optional**: Create a setup wizard to collect API keys on first launch.

## 🔧 Advanced Configuration

### Auto-Updates

Enable auto-updates by configuring `electron-updater`:

```javascript
// In electron/main.js
const { autoUpdater } = require('electron-updater');

autoUpdater.checkForUpdatesAndNotify();
```

Host updates on GitHub Releases or a custom server.

### Custom Installer

Modify NSIS configuration in `desktop-app/package.json`:

```json
{
  "build": {
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "installerHeader": "resources/installer-header.bmp",
      "installerSidebar": "resources/installer-sidebar.bmp"
    }
  }
}
```

### Code Signing

Sign your application for trusted distribution:

1. Get a code signing certificate
2. Configure in `package.json`:

```json
{
  "build": {
    "win": {
      "certificateFile": "path/to/certificate.pfx",
      "certificatePassword": "your_password"
    }
  }
}
```

## 🐛 Troubleshooting

### Backend Doesn't Start

**Issue**: Python backend fails to launch

**Solutions**:
- Check `api_server.exe` exists in `desktop-app/backend/`
- Verify all Python dependencies are included in PyInstaller build
- Check console logs in `%APPDATA%\windows-use-desktop\logs\`

### Frontend Shows 404

**Issue**: Frontend fails to load

**Solutions**:
- Verify `frontend-build` directory contains files
- Check that frontend server starts on port 3000
- Review Electron console logs (Ctrl+Shift+I in dev mode)

### Port Conflicts

**Issue**: Ports 8000 or 3000 already in use

**Solutions**:
- Configure different ports in `electron/main.js`
- Update frontend API endpoint in `frontend/src/`

### Large File Size

**Issue**: Installer is too large

**Solutions**:
- Use UPX compression in PyInstaller: `--upx-dir=/path/to/upx`
- Exclude unnecessary dependencies
- Use external Python runtime (requires users to install Python)

## 📊 Build Optimization

### Reduce Build Time

1. **Cache Dependencies**:
   ```bash
   npm ci  # Faster than npm install
   ```

2. **Skip Frontend Rebuild**:
   ```bash
   # Only rebuild backend
   cd desktop-app
   python build_backend.py
   npm run electron:build
   ```

3. **Parallel Builds**:
   Build backend and frontend simultaneously in separate terminals

### Reduce Installer Size

1. **Exclude Dev Dependencies**:
   ```json
   {
     "build": {
       "files": [
         "!node_modules/**/*",
         "node_modules/production-only/**/*"
       ]
     }
   }
   ```

2. **Compress Backend**:
   Use UPX to compress the Python executable

3. **Optimize Frontend**:
   ```bash
   cd frontend
   npm run build -- --experimental-app-dir
   ```

## 🎓 Best Practices

1. **Version Management**: Use semantic versioning (1.0.0, 1.1.0, 2.0.0)
2. **Changelog**: Maintain a CHANGELOG.md for user-facing changes
3. **Testing**: Test installer on clean Windows VM before release
4. **Documentation**: Include user guide and troubleshooting docs
5. **Support**: Set up GitHub Issues or Discord for user support

## 📝 Release Checklist

Before distributing your desktop app:

- [ ] Update version number in `package.json`
- [ ] Test installer on clean Windows system
- [ ] Verify terms & conditions are current
- [ ] Check all API integrations work
- [ ] Test uninstaller
- [ ] Create release notes
- [ ] Sign executable (optional but recommended)
- [ ] Upload to distribution platform (GitHub, website, etc.)
- [ ] Update documentation
- [ ] Announce release

## 🌟 Next Steps

After building your desktop app:

1. **Distribute**: Upload to GitHub Releases or your website
2. **Market**: Share on social media, product directories
3. **Support**: Set up user support channels
4. **Iterate**: Gather feedback and improve
5. **Update**: Push regular updates with new features

## 📞 Need Help?

- Check the [main README](../README.md)
- Join our [Discord](https://discord.com/invite/Aue9Yj2VzS)
- Open an [issue](https://github.com/CursorTouch/Windows-Use/issues)
- Follow [@CursorTouch](https://x.com/CursorTouch) on Twitter

---

**Ready to build?** Run `build.bat` and create your first desktop app! 🚀

