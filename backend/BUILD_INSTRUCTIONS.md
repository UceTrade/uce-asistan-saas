# PyInstaller Build Documentation

## 🚀 Quick Start

### 1. Install PyInstaller
```bash
pip install pyinstaller
```

### 2. Build Backend
```bash
cd backend
pyinstaller backend.spec --noconfirm
```

### 3. Test Output
```bash
cd dist
uceasistan-backend.exe
```

## 📦 Output Structure

After build:
```
backend/
├── dist/
│   └── uceasistan-backend.exe  ← Standalone executable (50-100 MB)
├── build/                       ← Temporary (can delete)
└── backend.spec                 ← Build configuration
```

## ⚙️ Configuration (backend.spec)

### Key Settings:
- **onefile**: Single exe (not folder)
- **console**: True (see logs)
- **upx**: Compression enabled
- **icon**: assets/icon.ico

### Hidden Imports:
All dependencies are automatically detected, but critical ones are explicitly listed:
- MetaTrader5
- websockets
- pandas/numpy
- fastapi/uvicorn

## 🔧 Electron Integration

### Update electron/main.js:

```javascript
function startBackend() {
    const isDev = !app.isPackaged;
    let backendPath;
    
    if (isDev) {
        // Development: Python script
        backendPath = path.join(__dirname, '../backend/start_server.py');
        backendProcess = spawn('python', [backendPath]);
    } else {
        // Production: Compiled exe
        backendPath = path.join(
            process.resourcesPath, 
            'backend/uceasistan-backend.exe'
        );
        backendProcess = spawn(backendPath);
    }
    
    console.log('[Electron] Backend started:', backendPath);
}
```

### Update package.json:

```json
{
  "build": {
    "extraResources": [
      {
        "from": "backend/dist/uceasistan-backend.exe",
        "to": "backend/uceasistan-backend.exe"
      }
    ]
  }
}
```

## 🧪 Testing

### Local Test (Before Electron):
```bash
# Terminal 1: Start backend
cd backend/dist
uceasistan-backend.exe

# Should output:
# WebSocket server started at ws://localhost:8766
# REST API server started at http://localhost:8080

# Terminal 2: Test connection
curl http://localhost:8080/api/v1/health
```

### Electron Test:
```bash
npm start
# Backend should auto-start
# Check DevTools console for logs
```

## 📊 Build Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution:** Add module to hiddenimports in backend.spec

### Issue: Exe too large (>150 MB)
**Solution:** 
- Enable UPX compression
- Exclude unnecessary modules (matplotlib, tkinter)

### Issue: Anti-virus flags exe
**Solution:**
- Code signing (requires certificate $100-300/year)
- Submit to vendors for whitelisting
- Add exclusion in Windows Defender

### Issue: Slow startup
**Solution:**
- Use --noupx for faster start (larger file)
- Consider Nuitka instead (compiles to C)

## 🎯 Production Checklist

- [ ] Build tested locally
- [ ] WebSocket server starts (port 8766)
- [ ] REST API responds (port 8080)
- [ ] MT5 connection works
- [ ] AI features functional
- [ ] Electron integration verified
- [ ] Full Setup.exe created
- [ ] Installer tested on clean Windows

## 🔄 Rebuild Process

When code changes:
```bash
cd backend
pyinstaller backend.spec --noconfirm --clean
```

## 📈 Next Steps

After PyInstaller success:
1. ✅ User doesn't need Python
2. 🔜 Add cloud monitoring (Railway/Render)
3. 🔜 7/24 strategy scanning
4. 🔜 Auto-update mechanism
