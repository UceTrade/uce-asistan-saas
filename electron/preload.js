/**
 * UceAsistan Electron Preload Script
 * Exposes safe APIs to the renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer
contextBridge.exposeInMainWorld('electronAPI', {
    // App info
    getVersion: () => ipcRenderer.invoke('get-app-version'),

    // Backend control
    restartBackend: () => ipcRenderer.invoke('restart-backend'),
    checkBackendStatus: () => ipcRenderer.invoke('check-backend-status'),

    // Update control
    checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
    quitAndInstall: () => ipcRenderer.invoke('quit-and-install'),

    // Update status listener
    onUpdateStatus: (callback) => {
        ipcRenderer.on('update-status', (event, message) => callback(message));
    },

    // External links
    openExternal: (url) => ipcRenderer.invoke('open-external-url', url),

    // Platform info
    platform: process.platform,
    isElectron: true,
    isPackaged: process.argv.includes('--packaged') || !process.defaultApp
});
