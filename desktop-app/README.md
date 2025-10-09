# Windows-Use Desktop Application

Build and distribution package for Windows-Use AI desktop application.

## 📦 What's Included

This package creates a standalone desktop application that bundles:
- Python backend (FastAPI server)
- Next.js frontend (React UI)
- Electron wrapper
- Windows installer (.exe)

## 🛠️ Prerequisites

Before building, ensure you have:

1. **Node.js** (v18 or higher)
   - Download from https://nodejs.org/

2. **Python** (3.12 or higher)
   - Download from https://www.python.org/
   - Ensure Python is added to PATH during installation

3. **Git** (for cloning the repository)
   - Download from https://git-scm.com/

## 🚀 Quick Build

### Automated Build (Recommended)

Simply run the build script:

```bash
build.bat
```

This script will:
1. Install all dependencies
2. Build the Python backend executable
3. Build the Next.js frontend
4. Package everything into an Electron app
5. Create a Windows installer

### Manual Build

If you prefer to build step by step:

```bash
# 1. Install desktop-app dependencies
cd desktop-app
npm install

# 2. Install PyInstaller
pip install pyinstaller

# 3. Build backend
python build_backend.py

# 4. Build frontend
cd ../frontend
npm install
npm run build

# 5. Copy frontend build
xcopy /E /I /Y "out" "..\desktop-app\frontend-build"

# 6. Build Electron installer
cd ../desktop-app
npm run electron:build
```

## 📁 Output

After building, you'll find:

- **Installer**: `desktop-app/dist/Windows-Use AI Setup X.X.X.exe`
- **Portable**: `desktop-app/dist/Windows-Use AI X.X.X.exe`

## 🎨 Customization

### Logo and Icons

Replace the following files with your custom branding:

- `resources/icon.ico` - Application icon (256x256 recommended)
- `resources/icon.png` - Application icon in PNG format

To generate icons from a PNG:

1. Use an online converter like https://convertico.com/
2. Generate .ico file with multiple sizes (16, 32, 48, 256)
3. Replace `resources/icon.ico`

### Terms and Conditions

Edit `electron/terms.html` to customize the terms and conditions page.

### App Metadata

Edit `package.json` to change:
- `name` - Application name
- `version` - Version number
- `description` - App description
- `author` - Author name
- `build.appId` - Unique app identifier
- `build.productName` - Display name

## 🔧 Development Mode

To test the desktop app without building:

```bash
cd desktop-app
npm run electron:dev
```

This will start the Electron app in development mode, loading the backend and frontend from source.

## 📝 Environment Variables

The desktop app requires a `.env` file in the project root with:

```env
GOOGLE_API_KEY=your_google_api_key_here
ENABLE_TTS=true
TTS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
DEEPGRAM_API_KEY=your_deepgram_key_here  # Optional, for voice control
```

Users will need to configure this after installation.

## 🐛 Troubleshooting

### Build Fails

1. **PyInstaller errors**: Ensure all Python dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Node.js errors**: Clear npm cache and reinstall
   ```bash
   npm cache clean --force
   cd desktop-app && npm install
   cd ../frontend && npm install
   ```

3. **Frontend build errors**: Check Next.js configuration
   ```bash
   cd frontend
   npm run build
   ```

### Runtime Errors

1. **Backend fails to start**: Check that `api_server.exe` exists in `desktop-app/backend/`

2. **Frontend doesn't load**: Verify `frontend-build` directory contains the built files

3. **Port conflicts**: Ensure ports 8000 and 3000 are available

## 📦 Distribution

The installer (`Windows-Use AI Setup X.X.X.exe`) includes:
- One-click installation
- Desktop shortcut creation
- Start menu entry
- Terms and conditions acceptance
- Uninstaller

The portable version requires no installation and runs from any location.

## 🔒 Security Notes

- The app requires administrator permissions for some Windows automation tasks
- API keys are stored locally and never transmitted to third parties
- Users should review the terms and conditions before use
- Recommend running in a sandbox environment for testing

## 📄 License

MIT License - See LICENSE.txt for details

## 🆘 Support

For issues and questions:
- GitHub: https://github.com/CursorTouch/Windows-Use
- Discord: https://discord.com/invite/Aue9Yj2VzS
- Twitter: @CursorTouch

