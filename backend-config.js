/**
 * Cloud Backend Configuration
 * Automatically connects to cloud backend if available, falls back to local
 */

// Backend URLs
const CLOUD_BACKEND = 'wss://YOUR-KOYEB-URL.koyeb.app'; // Koyeb deploy sonrası değiştir
const LOCAL_BACKEND = 'ws://localhost:8766';

// Determine which backend to use
function getBackendURL() {
    // Development mode: Always use local
    if (window.location.protocol === 'file:' || window.location.hostname === 'localhost') {
        return LOCAL_BACKEND;
    }

    // Production: Try cloud first, fallback to local
    return CLOUD_BACKEND;
}

// Export for use in mt5-connector.js
window.BACKEND_URL = getBackendURL();

console.log(`[Backend Config] Using: ${window.BACKEND_URL}`);
