/**
 * Auth Module - Login & Registration UI
 * Handles user authentication flow with Supabase
 */

// Import service (will be available globally in non-module context)
// import supabaseService from '../../services/supabase-service.js';

class AuthModule {
    constructor() {
        this.loginForm = null;
        this.registerForm = null;
        this.isLoading = false;
    }

    /**
     * Initialize auth module
     */
    init() {
        this.setupEventListeners();
        this.checkExistingSession();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Register form
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }

        // Tab switching
        document.querySelectorAll('[data-auth-tab]').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchTab(e.target.dataset.authTab));
        });
    }

    /**
     * Check for existing session
     */
    async checkExistingSession() {
        const service = window.supabaseService;
        if (!service) return;

        await service.init();

        if (service.isAuthenticated()) {
            this.hideAuthScreen();
            this.showMainApp();
        }
    }

    /**
     * Handle login form submission
     */
    async handleLogin(event) {
        event.preventDefault();
        if (this.isLoading) return;

        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        const errorEl = document.getElementById('loginError');

        if (!email || !password) {
            errorEl.textContent = 'Email ve şifre gerekli';
            return;
        }

        this.isLoading = true;
        this.setButtonLoading('loginBtn', true);
        errorEl.textContent = '';

        try {
            const service = window.supabaseService;
            const result = await service.login(email, password);

            if (result.success) {
                this.hideAuthScreen();
                this.showMainApp();
                this.showNotification('Giriş başarılı!', 'success');
            } else {
                errorEl.textContent = result.error || 'Giriş başarısız';
            }
        } catch (error) {
            errorEl.textContent = error.message;
        } finally {
            this.isLoading = false;
            this.setButtonLoading('loginBtn', false);
        }
    }

    /**
     * Handle register form submission
     */
    async handleRegister(event) {
        event.preventDefault();
        if (this.isLoading) return;

        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const fullName = document.getElementById('registerName').value;
        const errorEl = document.getElementById('registerError');

        if (!email || !password) {
            errorEl.textContent = 'Email ve şifre gerekli';
            return;
        }

        if (password.length < 6) {
            errorEl.textContent = 'Şifre en az 6 karakter olmalı';
            return;
        }

        this.isLoading = true;
        this.setButtonLoading('registerBtn', true);
        errorEl.textContent = '';

        try {
            const service = window.supabaseService;
            const result = await service.register(email, password, fullName);

            if (result.success) {
                this.showNotification(result.message || 'Kayıt başarılı! Email\'inizi kontrol edin.', 'success');
                this.switchTab('login');
            } else {
                errorEl.textContent = result.error || 'Kayıt başarısız';
            }
        } catch (error) {
            errorEl.textContent = error.message;
        } finally {
            this.isLoading = false;
            this.setButtonLoading('registerBtn', false);
        }
    }

    /**
     * Handle logout
     */
    async logout() {
        const service = window.supabaseService;
        await service.logout();

        this.showAuthScreen();
        this.hideMainApp();
        this.showNotification('Çıkış yapıldı', 'info');
    }

    /**
     * Switch between login and register tabs
     */
    switchTab(tab) {
        const loginTab = document.getElementById('loginTab');
        const registerTab = document.getElementById('registerTab');
        const loginForm = document.getElementById('loginFormContainer');
        const registerForm = document.getElementById('registerFormContainer');

        if (tab === 'login') {
            loginTab?.classList.add('active');
            registerTab?.classList.remove('active');
            loginForm?.classList.add('active');
            registerForm?.classList.remove('active');
        } else {
            loginTab?.classList.remove('active');
            registerTab?.classList.add('active');
            loginForm?.classList.remove('active');
            registerForm?.classList.add('active');
        }
    }

    /**
     * Show/hide auth screen
     */
    showAuthScreen() {
        const authScreen = document.getElementById('authScreen');
        if (authScreen) authScreen.style.display = 'flex';
    }

    hideAuthScreen() {
        const authScreen = document.getElementById('authScreen');
        if (authScreen) authScreen.style.display = 'none';
    }

    /**
     * Show/hide main app
     */
    showMainApp() {
        document.body.classList.remove('auth-hidden');
        const mainApp = document.getElementById('mainApp');
        if (mainApp) mainApp.style.display = 'block';
    }

    hideMainApp() {
        document.body.classList.add('auth-hidden');
        const mainApp = document.getElementById('mainApp');
        if (mainApp) mainApp.style.display = 'none';
    }

    /**
     * Set button loading state
     */
    setButtonLoading(buttonId, loading) {
        const btn = document.getElementById(buttonId);
        if (!btn) return;

        if (loading) {
            btn.disabled = true;
            btn.dataset.originalText = btn.textContent;
            btn.textContent = 'Yükleniyor...';
        } else {
            btn.disabled = false;
            btn.textContent = btn.dataset.originalText || 'Gönder';
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Use global notification function if available
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    /**
     * Get current user info
     */
    getCurrentUser() {
        return window.supabaseService?.getUser();
    }

    /**
     * Check if user has feature access
     */
    hasFeature(featureName) {
        return window.supabaseService?.hasFeature(featureName) || false;
    }
}

// Export
const authModule = new AuthModule();
export default authModule;

// Expose globally
if (typeof window !== 'undefined') {
    window.authModule = authModule;

    // Auto-initialize when DOM ready
    document.addEventListener('DOMContentLoaded', () => {
        authModule.init();
    });
}
