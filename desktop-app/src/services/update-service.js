/**
 * Update Service - Auto-update mechanism
 * Checks for updates and handles download/installation
 */

const UPDATE_API_URL = 'https://uceasistan-api.koyeb.app';
const CURRENT_VERSION = '2.3.0';

class UpdateService {
    constructor() {
        this.latestVersion = null;
        this.updateAvailable = false;
        this.changelog = null;
        this.downloadUrl = null;
    }

    /**
     * Check for available updates
     * @returns {Promise<{available: boolean, version: string, changelog: string}>}
     */
    async checkForUpdates() {
        try {
            const response = await fetch(`${UPDATE_API_URL}/api/version`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                timeout: 5000
            });

            if (!response.ok) {
                console.warn('[UpdateService] Version check failed:', response.status);
                return { available: false };
            }

            const data = await response.json();
            this.latestVersion = data.version;
            this.changelog = data.changelog || '';
            this.downloadUrl = data.download_url || '';

            // Compare versions
            this.updateAvailable = this.compareVersions(CURRENT_VERSION, this.latestVersion) < 0;

            if (this.updateAvailable) {
                console.log(`[UpdateService] Update available: ${CURRENT_VERSION} → ${this.latestVersion}`);
            }

            return {
                available: this.updateAvailable,
                version: this.latestVersion,
                changelog: this.changelog,
                downloadUrl: this.downloadUrl,
                currentVersion: CURRENT_VERSION
            };
        } catch (error) {
            console.error('[UpdateService] Check failed:', error);
            return { available: false, error: error.message };
        }
    }

    /**
     * Compare version strings
     * Returns: -1 if v1 < v2, 0 if equal, 1 if v1 > v2
     */
    compareVersions(v1, v2) {
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

    /**
     * Show update notification to user
     */
    showUpdateNotification() {
        if (!this.updateAvailable) return;

        const notification = document.createElement('div');
        notification.className = 'update-notification';
        notification.innerHTML = `
            <div class="update-notification-content">
                <div class="update-icon">🆕</div>
                <div class="update-info">
                    <h4>Yeni Güncelleme Mevcut!</h4>
                    <p>Versiyon ${this.latestVersion} kullanıma hazır</p>
                    ${this.changelog ? `<p class="changelog">${this.changelog}</p>` : ''}
                </div>
                <div class="update-actions">
                    <button class="btn btn-primary" onclick="updateService.startUpdate()">
                        Güncelle
                    </button>
                    <button class="btn btn-outline" onclick="this.parentElement.parentElement.parentElement.remove()">
                        Sonra
                    </button>
                </div>
            </div>
        `;

        // Add styles if not exists
        if (!document.getElementById('update-notification-styles')) {
            const style = document.createElement('style');
            style.id = 'update-notification-styles';
            style.textContent = `
                .update-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    border: 1px solid rgba(102, 126, 234, 0.3);
                    border-radius: 12px;
                    padding: 16px 20px;
                    z-index: 10000;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                    animation: slideIn 0.3s ease;
                    max-width: 400px;
                }
                .update-notification-content {
                    display: flex;
                    gap: 12px;
                    align-items: flex-start;
                }
                .update-icon {
                    font-size: 32px;
                }
                .update-info h4 {
                    margin: 0 0 4px 0;
                    color: #667eea;
                }
                .update-info p {
                    margin: 0;
                    font-size: 14px;
                    color: rgba(255,255,255,0.7);
                }
                .update-info .changelog {
                    font-size: 12px;
                    margin-top: 8px;
                    padding: 8px;
                    background: rgba(0,0,0,0.2);
                    border-radius: 6px;
                }
                .update-actions {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    margin-left: auto;
                }
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(notification);
    }

    /**
     * Start update process
     */
    async startUpdate() {
        if (!this.downloadUrl) {
            console.error('[UpdateService] No download URL available');
            return;
        }

        // For Electron apps, use shell to open download URL
        if (typeof require !== 'undefined') {
            const { shell } = require('electron');
            shell.openExternal(this.downloadUrl);
        } else {
            // For web, open in new tab
            window.open(this.downloadUrl, '_blank');
        }
    }

    /**
     * Get current version
     */
    getCurrentVersion() {
        return CURRENT_VERSION;
    }

    /**
     * Initialize - check for updates on startup
     */
    async init() {
        console.log(`[UpdateService] Current version: ${CURRENT_VERSION}`);

        // Check for updates after a short delay
        setTimeout(async () => {
            const result = await this.checkForUpdates();
            if (result.available) {
                this.showUpdateNotification();
            }
        }, 3000);
    }
}

// Export singleton
const updateService = new UpdateService();
export default updateService;

// Also expose globally
if (typeof window !== 'undefined') {
    window.updateService = updateService;
}
