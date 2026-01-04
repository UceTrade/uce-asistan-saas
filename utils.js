/**
 * Utility Functions - Formatters, Validators, Calculators, Notifications
 */

// ============================================
// FORMATTERS
// ============================================

/**
 * Format number as currency
 */
function formatCurrency(value, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

/**
 * Format number as percentage
 */
function formatPercent(value, decimals = 2) {
    return `${value.toFixed(decimals)}%`;
}

/**
 * Format date/time
 */
function formatDateTime(date) {
    if (typeof date === 'string') {
        date = new Date(date);
    }

    return new Intl.DateTimeFormat('tr-TR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

/**
 * Format large numbers with K, M, B suffixes
 */
function formatLargeNumber(value) {
    if (value >= 1000000000) {
        return (value / 1000000000).toFixed(2) + 'B';
    }
    if (value >= 1000000) {
        return (value / 1000000).toFixed(2) + 'M';
    }
    if (value >= 1000) {
        return (value / 1000).toFixed(2) + 'K';
    }
    return value.toFixed(2);
}

// ============================================
// VALIDATORS
// ============================================

/**
 * Validate email address
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate API key format
 */
function isValidApiKey(key) {
    return key && key.length >= 20;
}

/**
 * Validate MT5 credentials
 */
function validateMT5Credentials(login, password, server) {
    if (!login || login <= 0) {
        return { valid: false, message: 'Geçersiz giriş numarası' };
    }

    if (!password || password.length < 4) {
        return { valid: false, message: 'Şifre çok kısa' };
    }

    if (!server || server.length < 3) {
        return { valid: false, message: 'Geçersiz sunucu adı' };
    }

    return { valid: true };
}

/**
 * Validate number input
 */
function isValidNumber(value, min = null, max = null) {
    const num = parseFloat(value);

    if (isNaN(num)) return false;
    if (min !== null && num < min) return false;
    if (max !== null && num > max) return false;

    return true;
}

// ============================================
// CALCULATORS
// ============================================

/**
 * Calculate lot size based on risk
 */
function calculateLotSize(accountBalance, riskPercent, stopLossPips, pipValue) {
    const riskAmount = accountBalance * (riskPercent / 100);
    const lotSize = riskAmount / (stopLossPips * pipValue);
    return Math.round(lotSize * 100) / 100; // Round to 2 decimals
}

/**
 * Calculate pip value
 */
function calculatePipValue(symbol, lotSize = 1.0) {
    // Simplified calculation - in real app, would need actual exchange rates
    const majorPairs = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD'];

    if (majorPairs.includes(symbol)) {
        return 10 * lotSize; // $10 per pip for 1 lot
    }

    return 10 * lotSize; // Default
}

/**
 * Calculate risk/reward ratio
 */
function calculateRiskReward(entry, stopLoss, takeProfit) {
    const risk = Math.abs(entry - stopLoss);
    const reward = Math.abs(takeProfit - entry);

    if (risk === 0) return 0;

    return reward / risk;
}

/**
 * Calculate drawdown percentage
 */
function calculateDrawdown(balance, equity) {
    if (balance === 0) return 0;
    return ((balance - equity) / balance) * 100;
}

/**
 * Calculate profit percentage
 */
function calculateProfitPercent(initialBalance, currentProfit) {
    if (initialBalance === 0) return 0;
    return (currentProfit / initialBalance) * 100;
}

// ============================================
// NOTIFICATIONS
// ============================================

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icon = {
        success: '✅',
        danger: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    }[type] || 'ℹ️';

    toast.innerHTML = `
        <div style="font-size: 1.5rem;">${icon}</div>
        <div style="flex: 1;">${message}</div>
    `;

    container.appendChild(toast);

    // Auto remove after duration
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => {
            container.removeChild(toast);
        }, 300);
    }, duration);
}

/**
 * Show success notification
 */
function showSuccess(message) {
    showToast(message, 'success');
}

/**
 * Show error notification
 */
function showError(message) {
    showToast(message, 'danger', 5000);
}

/**
 * Show warning notification
 */
function showWarning(message) {
    showToast(message, 'warning', 4000);
}

/**
 * Show info notification
 */
function showInfo(message) {
    showToast(message, 'info');
}

// ============================================
// LOCAL STORAGE HELPERS
// ============================================

/**
 * Save to localStorage
 */
function saveToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (e) {
        console.error('LocalStorage kaydetme hatası:', e);
        return false;
    }
}

/**
 * Load from localStorage
 */
function loadFromStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
        console.error('LocalStorage yükleme hatası:', e);
        return defaultValue;
    }
}

/**
 * Remove from localStorage
 */
function removeFromStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (e) {
        console.error('LocalStorage silme hatası:', e);
        return false;
    }
}

/**
 * Clear all localStorage
 */
function clearStorage() {
    try {
        localStorage.clear();
        return true;
    } catch (e) {
        console.error('LocalStorage temizleme hatası:', e);
        return false;
    }
}

// ============================================
// DOM HELPERS
// ============================================

/**
 * Get element by ID safely
 */
function getElement(id) {
    return document.getElementById(id);
}

/**
 * Set element text content
 */
function setText(id, text) {
    const el = getElement(id);
    if (el) el.textContent = text;
}

/**
 * Set element HTML content
 */
function setHTML(id, html) {
    const el = getElement(id);
    if (el) el.innerHTML = html;
}

/**
 * Toggle element visibility
 */
function toggleElement(id) {
    const el = getElement(id);
    if (el) {
        el.classList.toggle('hidden');
    }
}

/**
 * Show element
 */
function showElement(id) {
    const el = getElement(id);
    if (el) {
        el.classList.remove('hidden');
        // Clear inline display: none if present, or force block if needed
        if (el.style.display === 'none') {
            el.style.display = '';
        }
    }
}

/**
 * Hide element
 */
function hideElement(id) {
    const el = getElement(id);
    if (el) {
        el.classList.add('hidden');
    }
}

// ============================================
// MISC HELPERS
// ============================================

/**
 * Generate unique ID
 */
function generateId() {
    return 'id_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Deep clone object
 */
function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

/**
 * Sleep/delay function
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Get risk level color
 */
function getRiskLevelColor(level) {
    const colors = {
        safe: 'var(--color-success)',
        caution: 'var(--color-warning)',
        warning: 'var(--color-accent-yellow)',
        danger: 'var(--color-danger)'
    };
    return colors[level] || colors.safe;
}

/**
 * Get risk level emoji
 */
function getRiskLevelEmoji(level) {
    const emojis = {
        safe: '🟢',
        caution: '🟡',
        warning: '🟠',
        danger: '🔴'
    };
    return emojis[level] || emojis.safe;
}

/**
 * Get risk level text
 */
function getRiskLevelText(level) {
    const texts = {
        safe: 'Güvenli Bölge',
        caution: 'Dikkat',
        warning: 'Uyarı',
        danger: 'Tehlike'
    };
    return texts[level] || texts.safe;
}
