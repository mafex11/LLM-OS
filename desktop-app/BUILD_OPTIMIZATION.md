# Electron Build Optimization Guide

## Overview

This document explains the optimizations made to reduce the Electron package size and ensure it works properly when packaged.

## Key Changes

### 1. Backend Size Reduction

**Problem**: PyInstaller was including massive libraries (torch, scipy, sklearn, etc.) that aren't needed for core functionality.

**Solution**: Updated `build_backend.py` to exclude unnecessary packages:
- `torch`, `torchaudio`, `torchvision` - ML frameworks (~2GB)
- `scipy`, `sklearn` - Scientific computing (~500MB)
- `matplotlib`, `IPython`, `jupyter` - Interactive tools (~200MB)
- `selenium`, `scrapy` - Web scraping tools (~100MB)

**Result**: Reduced backend size from ~3GB to ~500MB

### 2. Frontend Build Configuration

**Problem**: Next.js was outputting to `.next` but the build script was looking for `out` directory.

**Solution**: 
- Updated `next.config.js` to use `standalone` mode
- Updated build script to properly copy `.next/standalone` directory
- Configured Electron to run the standalone Next.js server

### 3. Electron Packaging Configuration

**Changes Made**:
- Enabled maximum compression in `package.json`
- Configured LZMA compression for NSIS installer
- Added `asarUnpack` for backend and frontend resources
- Optimized file inclusions

### 4. Runtime Improvements

**Changes to `main.js`**:
- Production mode now starts Next.js standalone server
- Proper path resolution for packaged vs development environments
- Better error handling and logging

## Building the Package

### Quick Start

```bash
cd desktop-app
build-optimized.bat
```

Or use the original build script:
```bash
cd ..
build.bat
```

### Build Process

1. **Backend Build** (~5-10 minutes)
   - Excludes large packages
   - Creates `api_server.exe` (~500MB instead of 3GB)

2. **Frontend Build** (~2-3 minutes)
   - Runs `next build` in standalone mode
   - Copies `.next/standalone` to `frontend-build`

3. **Electron Packaging** (~2-5 minutes)
   - Packages everything into installer
   - Applies LZMA compression
   - Creates installer in `dist/` folder

### Expected Package Sizes

- **Backend executable**: ~500MB (down from ~3GB)
- **Frontend build**: ~50MB
- **Electron app**: ~100MB (uncompressed)
- **Final installer**: ~200-300MB (with LZMA compression)

## Development vs Production

### Development Mode
```bash
npm run electron:dev
```
- Runs Next.js dev server
- Runs Python backend directly
- Hot reload enabled

### Production Package
```bash
npm run electron:build
```
- Runs Next.js standalone server
- Runs PyInstaller executable
- All dependencies bundled

## Troubleshooting

### "The system cannot find the path specified"
- Make sure you're running from the correct directory
- Check that all dependencies are installed

### Frontend not loading in packaged app
- Check that `.next/standalone` directory was copied
- Look for logs in `logs/electron-main.log`
- Verify backend is running on port 8000

### Large package size
- Check that exclusions in `build_backend.py` are working
- Verify compression is enabled in `package.json`
- Make sure `standalone` mode is used for Next.js

### App crashes on startup
- Check backend logs: `logs/api_server.log`
- Check Electron logs: `desktop-app/logs/electron-main.log`
- Ensure API keys are configured in `config/api_keys.json`

## File Structure

```
desktop-app/
├── backend/
│   └── api_server.exe          # PyInstaller executable
├── frontend-build/
│   ├── server.js               # Next.js standalone server
│   ├── .next/                  # Next.js build files
│   ├── node_modules/           # Production dependencies
│   └── public/                 # Static assets
├── electron/
│   ├── main.js                 # Main Electron process
│   ├── preload.js              # Preload script
│   └── data-paths.js           # Data path management
├── resources/                  # Icons, licenses
└── dist/                       # Final installer
    └── *.exe                   # Installer package
```

## Architecture

When the packaged app runs:

1. **Electron main process** (`main.js`) starts
2. **Backend server** (`api_server.exe`) starts on port 8000
3. **Frontend server** (Next.js standalone) starts on port 3000
4. **BrowserWindow** loads `http://localhost:3000`
5. Frontend makes API calls to `http://localhost:8000`

## Performance Notes

- Startup time: ~10-15 seconds (includes backend initialization)
- Memory usage: ~500MB baseline (backend + frontend)
- Package size: ~200-300MB installer
- Install size: ~1GB (includes all resources)

## Next Steps for Further Optimization

1. **Tree-shake frontend**: Remove unused React components
2. **Minify Python imports**: Only import what's needed
3. **Shared dependencies**: Use Electron's bundled Node.js for Next.js
4. **Dynamic imports**: Load heavy modules on-demand
5. **WebAssembly**: Replace some Python code with WASM

## Configuration Files

- `build_backend.py`: Backend build configuration
- `next.config.js`: Frontend build configuration
- `package.json`: Electron build configuration
- `build-optimized.bat`: Optimized build script
- `main.js`: Runtime configuration

## Support

For issues or questions, check:
- Backend logs: `logs/api_server.log`
- Electron logs: `desktop-app/logs/electron-main.log`
- Build output: Terminal output during build






