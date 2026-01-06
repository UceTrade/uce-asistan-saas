/**
 * UceAsistan - Notification System
 * Centralized toast/notification management
 */

(function () {
    'use strict';

    const NOTIFICATION_DURATION = 4000;
    const MAX_NOTIFICATIONS = 5;

    let container = null;

    /**
     * Get or create notification container
     */
    function getContainer() {
        if (!container) {
            container = document.getElementById('toastContainer');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toastContainer';
                container.className = 'toast-container';
                document.body.appendChild(container);
            }
        }
        return container;
    }

    /**
     * Create and show a notification
     */
    function show(message, type = 'info', duration = NOTIFICATION_DURATION) {
        const container = getContainer();

        // Limit max notifications
        while (container.children.length >= MAX_NOTIFICATIONS) {
            container.firstChild.remove();
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
        `;

        container.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.classList.add('toast-show');
        });

        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.remove('toast-show');
                toast.classList.add('toast-hide');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }

        return toast;
    }

    // Convenience methods
    const notify = {
        success: (msg, duration) => show(msg, 'success', duration),
        error: (msg, duration) => show(msg, 'error', duration),
        warning: (msg, duration) => show(msg, 'warning', duration),
        info: (msg, duration) => show(msg, 'info', duration),
        show
    };

    // Legacy global function support
    window.showSuccess = notify.success;
    window.showError = notify.error;
    window.showWarning = notify.warning;
    window.showInfo = notify.info;

    // Modern API
    window.UceAsistan = window.UceAsistan || {};
    window.UceAsistan.notify = notify;

})();
