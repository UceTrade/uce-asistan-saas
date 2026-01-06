/**
 * UceAsistan Electron Main Process
 * Handles window creation, backend process management, and auto-updates
 * Uses electron-updater for seamless automatic updates
 */

const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

// Auto-updater (only in production)
let autoUpdater = null;
if (app.isPackaged) {
    try {
        const { autoUpdater: updater } = require('electron-updater');
        autoUpdater = updater;
        autoUpdater.logger = require('electron-log');
        autoUpdater.logger.transports.file.level = 'info';
    } catch (e) {
        console.log('[Update] electron-updater not available');
    }
}

// Configuration
const CURRENT_VERSION = require('../package.json').version || '2.3.0';
const FALLBACK_UPDATE_URL = 'https://uceasistan-api.koyeb.app/api/version';

let mainWindow;
let backendProcess = null;

// Create the main application window
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1200,
        minHeight: 700,
        title: 'UceAsistan',
        icon: path.join(__dirname, '../assets/icon.ico'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        autoHideMenuBar: true,
        show: false
    });

    mainWindow.loadFile('index.html');

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        mainWindow.focus();

        // Check for updates
        checkForUpdates();

        // Open DevTools in development
        if (!app.isPackaged) {
            mainWindow.webContents.openDevTools();
        }
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
        stopBackend();
    });
}

// Start Python backend server
function startBackend() {
    const isDev = !app.isPackaged;
    const fs = require('fs');

    let backendCmd;
    let backendArgs = [];
    let backendCwd;

    if (isDev) {
        // Development mode - use Python
        backendCmd = 'python';
        backendArgs = [path.join(__dirname, '../backend/start_server.py')];
        backendCwd = path.join(__dirname, '../backend');
    } else {
        // Production mode - use bundled EXE
        const backendExe = path.join(process.resourcesPath, 'backend', 'uceasistan_backend.exe');

        if (fs.existsSync(backendExe)) {
            backendCmd = backendExe;
            backendCwd = path.join(process.resourcesPath, 'backend');
            console.log('[Electron] Using bundled backend EXE');
        } else {
            // Fallback to Python if EXE not found
            console.warn('[Electron] Backend EXE not found, trying Python');
            backendCmd = 'python';
            backendArgs = [path.join(process.resourcesPath, 'backend/start_server.py')];
            backendCwd = path.join(process.resourcesPath, 'backend');
        }
    }

    console.log('[Electron] Starting backend:', backendCmd);

    backendProcess = spawn(backendCmd, backendArgs, {
        cwd: backendCwd,
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    backendProcess.stdout.on('data', (data) => {
        console.log(`[Backend] ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
        console.error(`[Backend Error] ${data}`);
    });

    backendProcess.on('close', (code) => {
        console.log(`[Backend] Process exited with code ${code}`);
        backendProcess = null;
    });

    backendProcess.on('error', (err) => {
        console.error('[Backend] Failed to start:', err);
        dialog.showErrorBox(
            'Backend Hatası',
            'Backend başlatılamadı. Lütfen uygulamayı yeniden yükleyin.'
        );
    });
}

// Stop Python backend
function stopBackend() {
    if (backendProcess) {
        console.log('[Electron] Stopping backend...');
        backendProcess.kill();
        backendProcess = null;
    }
}

// ============================================
// AUTO-UPDATE SYSTEM
// ============================================

function checkForUpdates() {
    if (!app.isPackaged) {
        console.log('[Update] Skipping update check in development mode');
        return;
    }

    // Use electron-updater if available
    if (autoUpdater) {
        setupAutoUpdater();
        autoUpdater.checkForUpdatesAndNotify();
    } else {
        // Fallback to manual check
        checkForUpdatesManual();
    }
}

function setupAutoUpdater() {
    autoUpdater.on('checking-for-update', () => {
        console.log('[Update] Checking for updates...');
        sendStatusToWindow('Güncelleme kontrol ediliyor...');
    });

    autoUpdater.on('update-available', (info) => {
        console.log('[Update] Update available:', info.version);
        sendStatusToWindow(`Yeni sürüm mevcut: ${info.version}`);

        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: '🆕 Güncelleme Mevcut',
            message: `Yeni versiyon ${info.version} mevcut!`,
            detail: 'İndirme otomatik olarak başlayacak.',
            buttons: ['Tamam']
        });
    });

    autoUpdater.on('update-not-available', (info) => {
        console.log('[Update] Already on latest version');
    });

    autoUpdater.on('error', (err) => {
        console.error('[Update] Error:', err);
        sendStatusToWindow('Güncelleme hatası');
    });

    autoUpdater.on('download-progress', (progressObj) => {
        const percent = Math.round(progressObj.percent);
        console.log(`[Update] Downloaded ${percent}%`);
        sendStatusToWindow(`İndiriliyor: ${percent}%`);

        if (mainWindow) {
            mainWindow.setProgressBar(progressObj.percent / 100);
        }
    });

    autoUpdater.on('update-downloaded', (info) => {
        console.log('[Update] Update downloaded');
        sendStatusToWindow('Güncelleme indirildi');

        if (mainWindow) {
            mainWindow.setProgressBar(-1); // Remove progress bar
        }

        dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: '✅ Güncelleme Hazır',
            message: `Versiyon ${info.version} indirildi`,
            detail: 'Uygulamayı şimdi yeniden başlatarak güncelleyin.',
            buttons: ['Şimdi Yeniden Başlat', 'Sonra'],
            defaultId: 0,
            cancelId: 1
        }).then((result) => {
            if (result.response === 0) {
                autoUpdater.quitAndInstall();
            }
        });
    });
}

function sendStatusToWindow(text) {
    if (mainWindow) {
        mainWindow.webContents.send('update-status', text);
    }
}

// Manual update check (fallback)
function checkForUpdatesManual() {
    const https = require('https');

    console.log('[Update] Manual check from:', FALLBACK_UPDATE_URL);
    console.log('[Update] Current version:', CURRENT_VERSION);

    const req = https.get(FALLBACK_UPDATE_URL, (res) => {
        let data = '';

        res.on('data', (chunk) => {
            data += chunk;
        });

        res.on('end', () => {
            try {
                const updateInfo = JSON.parse(data);
                const latestVersion = updateInfo.version;

                console.log('[Update] Latest version:', latestVersion);

                if (compareVersions(CURRENT_VERSION, latestVersion) < 0) {
                    showManualUpdateNotification(updateInfo);
                } else {
                    console.log('[Update] Already on latest version');
                }
            } catch (error) {
                console.error('[Update] Parse error:', error);
            }
        });
    });

    req.on('error', (error) => {
        console.error('[Update] Check failed:', error);
    });

    req.setTimeout(10000, () => {
        req.destroy();
        console.error('[Update] Request timeout');
    });
}

function compareVersions(v1, v2) {
    const parts1 = v1.split('.').map(Number);
    const parts2 = v2.split('.').map(Number);

    for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
        const p1 = parts1[i] || 0;
        const p2 = parts2[i] || 0;

        if (p1 < p2) return -1;
        if (p1 > p2) return 1;
    }
    return 0;
}

function showManualUpdateNotification(updateInfo) {
    dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: '🆕 Güncelleme Mevcut',
        message: `Yeni versiyon ${updateInfo.version} mevcut!`,
        detail: updateInfo.changelog || 'Performans iyileştirmeleri ve hata düzeltmeleri.',
        buttons: ['İndir', 'Sonra'],
        defaultId: 0,
        cancelId: 1
    }).then((result) => {
        if (result.response === 0) {
            if (updateInfo.download_url) {
                shell.openExternal(updateInfo.download_url);
            }
        }
    });
}

// ============================================
// APP LIFECYCLE
// ============================================

app.whenReady().then(() => {
    createWindow();
    startBackend();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    stopBackend();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    stopBackend();
});

// ============================================
// IPC HANDLERS
// ============================================

ipcMain.handle('get-app-version', () => {
    return CURRENT_VERSION;
});

ipcMain.handle('restart-backend', () => {
    stopBackend();
    setTimeout(() => startBackend(), 1000);
    return true;
});

ipcMain.handle('check-backend-status', () => {
    return backendProcess !== null && !backendProcess.killed;
});

ipcMain.handle('check-for-updates', () => {
    checkForUpdates();
    return true;
});

ipcMain.handle('open-external-url', (event, url) => {
    shell.openExternal(url);
    return true;
});

ipcMain.handle('quit-and-install', () => {
    if (autoUpdater) {
        autoUpdater.quitAndInstall();
    }
    return true;
});
