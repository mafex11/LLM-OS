# ⚡ Quick Reference - Desktop App

## Build Commands

```bash
# Quick setup
cd desktop-app
quick-start.bat

# Full build (from project root)
build.bat

# Development mode
cd desktop-app
npm run electron:dev

# Build only backend
python build_backend.py

# Build only frontend
cd frontend && npm run build

# Create installer only (after building backend and frontend)
cd desktop-app
npm run electron:build
```

## File Locations

| Item | Path |
|------|------|
| Installer output | `desktop-app/dist/` |
| Backend executable | `desktop-app/backend/api_server.exe` |
| Frontend build | `desktop-app/frontend-build/` |
| App icon | `desktop-app/resources/icon.ico` |
| Terms page | `desktop-app/electron/terms.html` |

## Customization

### Change App Name
Edit `desktop-app/package.json`:
```json
{
  "name": "your-app-name",
  "build": {
    "productName": "Your App Display Name"
  }
}
```

### Change Icon
```bash
# Use custom logo
cd desktop-app
python create_icons.py path/to/logo.png

# Or replace manually
# desktop-app/resources/icon.ico
# desktop-app/resources/icon.png
```

### Update Terms
Edit `desktop-app/electron/terms.html`

### Change Version
Edit `desktop-app/package.json`:
```json
{
  "version": "1.0.0"
}
```

## Common Issues

| Problem | Solution |
|---------|----------|
| PyInstaller fails | `pip install --upgrade pyinstaller` |
| Node modules error | `cd desktop-app && npm install` |
| Icon not showing | Run `create_icons.py` again |
| Backend won't start | Check `.env` file exists with API key |
| Port conflict | Close apps using ports 8000, 3000 |

## Ports Used

- **8000**: Python backend (FastAPI)
- **3000**: Next.js frontend

## Environment Variables

Required in `.env`:
```env
GOOGLE_API_KEY=your_key
ENABLE_TTS=true  # optional
```

## Build Output

After successful build:
```
desktop-app/
└── dist/
    ├── Windows-Use AI Setup 1.0.0.exe  # Installer
    └── Windows-Use AI 1.0.0.exe        # Portable
```

## Development Workflow

1. **Make changes** to code
2. **Test** in dev mode: `npm run electron:dev`
3. **Build** when ready: `build.bat`
4. **Test installer** on clean VM
5. **Distribute** the installer

## User Installation

Users download and run:
1. `Windows-Use AI Setup 1.0.0.exe`
2. Follow installer
3. Accept terms
4. Create `.env` with API key
5. Launch and use

## Distribution Checklist

- [ ] Update version in `package.json`
- [ ] Custom logo/icon added
- [ ] Terms updated
- [ ] Full build tested
- [ ] Installer tested on clean Windows
- [ ] Release notes prepared
- [ ] Uploaded to distribution platform

---

For detailed info, see:
- Developer: `DESKTOP_APP_GUIDE.md`
- Users: `SETUP_GUIDE.md`

