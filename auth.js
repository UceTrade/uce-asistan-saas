/**
 * UceAsistan Auth - Refactored with Demo Mode Support
 * Provides authentication, subscription management, and feature gating
 * 
 * Architecture:
 * - Demo Mode: Works offline without any backend (default for local development)
 * - Supabase Mode: Full cloud authentication when configured
 */

// ============================================
// SUBSCRIPTION TIER DEFINITIONS
// ============================================

const SUBSCRIPTION_TIERS = {
    free: {
        name: 'Free',
        displayName: 'Ücretsiz Plan',
        maxStrategies: 3,
        maxSymbols: 5,
        features: ['basic_analysis', 'dashboard', 'manual_trading'],
        aiRequests: 10,
        liveTrading: false,
        confluenceRadar: false,
        propFirmRules: false,
        telegram: false,
        color: '#a0aec0'
    },
    pro: {
        name: 'Pro',
        displayName: 'Profesyonel Plan',
        maxStrategies: 20,
        maxSymbols: 30,
        features: ['basic_analysis', 'dashboard', 'manual_trading', 'ai_strategy', 'backtest', 'confluence_radar', 'prop_firm', 'neural_pulse'],
        aiRequests: 500,
        liveTrading: true,
        confluenceRadar: true,
        propFirmRules: true,
        telegram: true,
        color: '#667eea'
    },
    enterprise: {
        name: 'Enterprise',
        displayName: 'Kurumsal Plan',
        maxStrategies: -1,
        maxSymbols: -1,
        features: ['all'],
        aiRequests: -1,
        liveTrading: true,
        confluenceRadar: true,
        propFirmRules: true,
        telegram: true,
        multiAccount: true,
        prioritySupport: true,
        color: '#f093fb'
    }
};

// ============================================
// AUTH CONFIGURATION
// ============================================

const AUTH_CONFIG = {
    // Set to false to enable Supabase mode (cloud authentication)
    // Set to true for local development without backend
    demoMode: false,

    // Demo user credentials (works without any backend)
    demoCredentials: {
        email: 'demo@uceasistan.com',
        password: 'demo123'
    },

    // Supabase configuration (active when demoMode is false)
    supabase: {
        url: 'https://eksixzptfnmfvjdigeiy.supabase.co',
        anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVrc2l4enB0Zm5tZnZqZGlnZWl5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc1MzEyMTAsImV4cCI6MjA4MzEwNzIxMH0.7g3nJvKobAl5ZRvQnuIql47bEw9bT4NpqyK0Afqwqmw'
    },

    // Storage keys
    storageKeys: {
        session: 'uce_session',
        settings: 'uce_settings'
    }
};

// ============================================
// AUTH CLASS
// ============================================

class UceAuth {
    constructor() {
        this.supabase = null;
        this.user = null;
        this.initialized = false;
        this.mode = 'demo'; // 'demo' or 'supabase'
    }

    /**
     * Initialize authentication
     */
    async init() {
        console.log('[Auth] Initializing...');

        // Check for existing session first
        if (this.loadFromStorage()) {
            console.log('[Auth] Session restored from storage');
            this.initialized = true;
            return;
        }

        // Try Supabase initialization if not in demo mode
        if (!AUTH_CONFIG.demoMode && window.supabase) {
            try {
                this.supabase = window.supabase.createClient(
                    AUTH_CONFIG.supabase.url,
                    AUTH_CONFIG.supabase.anonKey
                );
                this.mode = 'supabase';
                console.log('[Auth] Supabase client initialized');

                // Check for existing Supabase session
                const { data: { session } } = await this.supabase.auth.getSession();
                if (session) {
                    await this.loadUserFromSession(session);
                }

                // Listen for auth changes
                this.supabase.auth.onAuthStateChange(async (event, session) => {
                    if (event === 'SIGNED_IN' && session) {
                        await this.loadUserFromSession(session);
                    } else if (event === 'SIGNED_OUT') {
                        this.clearSession();
                    }
                });
            } catch (error) {
                console.warn('[Auth] Supabase init failed, falling back to demo mode:', error);
                this.mode = 'demo';
            }
        } else {
            this.mode = 'demo';
            console.log('[Auth] Running in Demo Mode (no backend required)');
        }

        this.initialized = true;
    }

    /**
     * Login with email and password
     */
    async login(email, password) {
        console.log(`[Auth] Login attempt: ${email}`);

        // Demo mode login
        if (this.mode === 'demo') {
            return this.demoLogin(email, password);
        }

        // Supabase login
        try {
            const { data, error } = await this.supabase.auth.signInWithPassword({
                email,
                password
            });

            if (error) {
                return { success: false, error: error.message };
            }

            await this.loadUserFromSession(data.session);
            return { success: true, user: this.user };
        } catch (e) {
            console.error('[Auth] Login error:', e);
            return { success: false, error: 'Bağlantı hatası: ' + e.message };
        }
    }

    /**
     * Demo mode login - works offline
     */
    demoLogin(email, password) {
        // Accept any email/password in demo mode for development
        // In production, you would validate against demo credentials
        const isDemo = email === AUTH_CONFIG.demoCredentials.email &&
            password === AUTH_CONFIG.demoCredentials.password;

        // For development, accept any login
        const allowAny = AUTH_CONFIG.demoMode && email.includes('@');

        if (isDemo || allowAny) {
            this.user = this.createDemoUser(email);
            this.saveToStorage();
            console.log('[Auth] Demo login successful');
            return { success: true, user: this.user };
        }

        return {
            success: false,
            error: `Demo mod için: ${AUTH_CONFIG.demoCredentials.email} / ${AUTH_CONFIG.demoCredentials.password}`
        };
    }

    /**
     * Create a demo user object
     */
    createDemoUser(email) {
        const expiry = new Date();
        expiry.setDate(expiry.getDate() + 30); // 30 day unlimited trial

        return {
            id: 'demo_' + Date.now(),
            email: email,
            status: 'active',
            isDemo: true,
            subscription: {
                tier: 'enterprise', // Full access in demo
                plan: SUBSCRIPTION_TIERS.enterprise.displayName,
                expiry: expiry.toISOString().split('T')[0],
                isActive: true,
                isTrial: true,
                trialDaysLeft: 30,
                aiRequestsUsed: 0,
                aiRequestsLimit: -1 // Unlimited
            }
        };
    }

    /**
     * Register new user
     */
    async register(email, password, fullName = '') {
        if (this.mode === 'demo') {
            // In demo mode, just log them in
            return this.demoLogin(email, password);
        }

        try {
            const { data, error } = await this.supabase.auth.signUp({
                email,
                password,
                options: { data: { full_name: fullName } }
            });

            if (error) {
                return { success: false, error: error.message };
            }

            return {
                success: true,
                message: 'Kayıt başarılı! E-posta adresinizi doğrulayın.',
                user: data.user
            };
        } catch (e) {
            return { success: false, error: e.message };
        }
    }

    /**
     * Logout
     */
    async logout() {
        if (this.supabase) {
            await this.supabase.auth.signOut();
        }
        this.clearSession();
        window.location.reload();
    }

    /**
     * Load user from Supabase session
     */
    async loadUserFromSession(session) {
        const { user: authUser } = session;

        let profile = null;
        if (this.supabase) {
            const { data } = await this.supabase
                .from('profiles')
                .select('*')
                .eq('id', authUser.id)
                .single();
            profile = data;
        }

        const tier = profile?.subscription_tier || 'pro';

        this.user = {
            id: authUser.id,
            email: authUser.email,
            status: 'active',
            isDemo: false,
            subscription: {
                tier: tier,
                plan: SUBSCRIPTION_TIERS[tier].displayName,
                expiry: profile?.subscription_expires_at || this.getTrialExpiry(),
                isActive: true,
                isTrial: !profile?.subscription_expires_at,
                trialDaysLeft: 7,
                aiRequestsUsed: profile?.ai_requests_used || 0,
                aiRequestsLimit: SUBSCRIPTION_TIERS[tier].aiRequests
            }
        };

        this.saveToStorage();
    }

    /**
     * Get trial expiry date (7 days from now)
     */
    getTrialExpiry() {
        const expiry = new Date();
        expiry.setDate(expiry.getDate() + 7);
        return expiry.toISOString().split('T')[0];
    }

    // ============================================
    // FEATURE ACCESS CONTROL
    // ============================================

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return this.user !== null;
    }

    /**
     * Check subscription status
     */
    async checkSubscription() {
        if (!this.user) return false;

        const now = new Date();
        const expiry = new Date(this.user.subscription.expiry);

        if (expiry < now) {
            this.user.subscription.isActive = false;
            this.user.subscription.tier = 'free';
            this.saveToStorage();
            return false;
        }

        return true;
    }

    /**
     * Check if user has access to a specific feature
     */
    hasFeature(featureName) {
        if (!this.user) return false;

        const tier = this.user.subscription?.tier || 'free';
        const tierConfig = SUBSCRIPTION_TIERS[tier];

        if (!tierConfig) return false;
        if (tierConfig.features.includes('all')) return true;

        return tierConfig.features.includes(featureName);
    }

    /**
     * Check if a specific feature can be used
     */
    canUseFeature(featureName) {
        if (!this.user) {
            return { allowed: false, reason: 'Giriş yapmanız gerekiyor' };
        }

        if (!this.user.subscription.isActive) {
            return { allowed: false, reason: 'Aboneliğiniz sona ermiş' };
        }

        if (!this.hasFeature(featureName)) {
            return {
                allowed: false,
                reason: `Bu özellik ${SUBSCRIPTION_TIERS.pro.displayName} ve üzeri planlarda geçerlidir`,
                upgradeRequired: true
            };
        }

        return { allowed: true };
    }

    /**
     * Get remaining AI requests
     */
    getRemainingAIRequests() {
        if (!this.user) return 0;

        const tier = this.user.subscription?.tier || 'free';
        const limit = SUBSCRIPTION_TIERS[tier].aiRequests;

        if (limit === -1) return Infinity;

        const used = this.user.subscription.aiRequestsUsed || 0;
        return Math.max(0, limit - used);
    }

    /**
     * Consume an AI request
     */
    consumeAIRequest() {
        if (!this.user) return false;

        const remaining = this.getRemainingAIRequests();
        if (remaining <= 0 && remaining !== Infinity) return false;

        this.user.subscription.aiRequestsUsed = (this.user.subscription.aiRequestsUsed || 0) + 1;
        this.saveToStorage();
        return true;
    }

    /**
     * Get current tier configuration
     */
    getTierConfig() {
        const tier = this.user?.subscription?.tier || 'free';
        return SUBSCRIPTION_TIERS[tier];
    }

    /**
     * Get all tier configurations
     */
    getAllTiers() {
        return SUBSCRIPTION_TIERS;
    }

    /**
     * Update subscription tier
     */
    async updateSubscriptionTier(newTier) {
        if (!SUBSCRIPTION_TIERS[newTier]) {
            return { success: false, error: 'Geçersiz paket' };
        }

        if (this.user) {
            this.user.subscription.tier = newTier;
            this.user.subscription.plan = SUBSCRIPTION_TIERS[newTier].displayName;
            this.user.subscription.isActive = true;
            this.user.subscription.aiRequestsLimit = SUBSCRIPTION_TIERS[newTier].aiRequests;

            const expiry = new Date();
            expiry.setFullYear(expiry.getFullYear() + 1);
            this.user.subscription.expiry = expiry.toISOString().split('T')[0];
            this.user.subscription.isTrial = false;

            this.saveToStorage();
        }

        // Update Supabase if connected
        if (this.supabase && this.user && !this.user.isDemo) {
            try {
                await this.supabase
                    .from('profiles')
                    .update({
                        subscription_tier: newTier,
                        subscription_expires_at: this.user.subscription.expiry
                    })
                    .eq('id', this.user.id);
            } catch (error) {
                console.warn('[Auth] Supabase update failed:', error);
            }
        }

        return { success: true, tier: newTier };
    }

    // ============================================
    // STORAGE HELPERS
    // ============================================

    saveToStorage() {
        try {
            localStorage.setItem(AUTH_CONFIG.storageKeys.session, JSON.stringify(this.user));
        } catch (e) {
            console.warn('[Auth] Storage save failed:', e);
        }
    }

    loadFromStorage() {
        try {
            const stored = localStorage.getItem(AUTH_CONFIG.storageKeys.session);
            if (stored) {
                this.user = JSON.parse(stored);
                this.checkSubscription();
                return true;
            }
        } catch (e) {
            console.warn('[Auth] Storage load failed:', e);
        }
        return false;
    }

    clearSession() {
        this.user = null;
        try {
            localStorage.removeItem(AUTH_CONFIG.storageKeys.session);
        } catch (e) {
            console.warn('[Auth] Storage clear failed:', e);
        }
    }

    /**
     * Check for expiration warning
     */
    checkExpirationWarning() {
        if (!this.user) return null;

        const now = new Date();
        const expiry = new Date(this.user.subscription.expiry);
        const daysLeft = Math.ceil((expiry - now) / (1000 * 60 * 60 * 24));

        if (daysLeft <= 0) {
            return { level: 'expired', message: 'Aboneliğiniz sona erdi!', daysLeft: 0 };
        } else if (daysLeft <= 3) {
            return { level: 'critical', message: `Aboneliğiniz ${daysLeft} gün içinde sona erecek!`, daysLeft };
        } else if (daysLeft <= 7) {
            return { level: 'warning', message: `Aboneliğiniz ${daysLeft} gün sonra sona erecek`, daysLeft };
        }
        return null;
    }

    /**
     * Check session status (for backward compatibility)
     */
    checkSession() {
        return this.loadFromStorage();
    }
}

// ============================================
// GLOBAL INITIALIZATION
// ============================================

// Create global instance
window.uceAuth = new UceAuth();

// Export tier definitions
window.SUBSCRIPTION_TIERS = SUBSCRIPTION_TIERS;

// Export auth config for external access
window.AUTH_CONFIG = AUTH_CONFIG;

// Helper function to show upgrade modal
window.showUpgradeModal = function (featureName) {
    const message = `"${featureName}" özelliği Pro ve üzeri planlarda kullanılabilir.`;

    if (typeof showWarning === 'function') {
        showWarning(message);
    } else if (typeof alert === 'function') {
        alert(message);
    }
};

console.log('[Auth] Module loaded. Demo mode:', AUTH_CONFIG.demoMode);
