/**
 * UceAsistan Auth - Membership, Subscription Tiers, and Feature Gating
 */

// Subscription Tier Definitions
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
        maxStrategies: -1, // Unlimited
        maxSymbols: -1, // Unlimited
        features: ['all'],
        aiRequests: -1, // Unlimited
        liveTrading: true,
        confluenceRadar: true,
        propFirmRules: true,
        telegram: true,
        multiAccount: true,
        prioritySupport: true,
        color: '#f093fb'
    }
};

class UceAuth {
    constructor() {
        // Supabase credentials - Production values
        this.supabaseUrl = 'https://eksixzptfnmfvjdigeiy.supabase.co';
        this.supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVrc2l4enB0Zm5tZnZqZGlnZWl5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc1MzEyMTAsImV4cCI6MjA4MzEwNzIxMH0.7g3nJvKobAl5ZRvQnuIql47bEw9bT4NpqyK0Afqwqmw';
        this.supabase = null;
        this.user = null;
        this.initialized = false;
    }

    async init() {
        // Try to initialize Supabase if credentials are provided
        if (this.supabaseUrl && this.supabaseKey && window.supabase) {
            try {
                this.supabase = window.supabase.createClient(this.supabaseUrl, this.supabaseKey);
                console.log('✅ Supabase client initialized');

                // Check for existing session
                const { data: { session } } = await this.supabase.auth.getSession();
                if (session) {
                    await this.loadUserFromSession(session);
                }

                // Listen for auth changes
                this.supabase.auth.onAuthStateChange(async (event, session) => {
                    console.log('Auth state changed:', event);
                    if (event === 'SIGNED_IN' && session) {
                        await this.loadUserFromSession(session);
                    } else if (event === 'SIGNED_OUT') {
                        this.user = null;
                        removeFromStorage('uce_session');
                    }
                });
            } catch (error) {
                console.error('Supabase init error:', error);
            }
        } else {
            console.warn('⚠️ Supabase credentials missing. Running in DEV/GUEST mode.');
            console.info('📖 See docs/SUPABASE_SETUP.md for setup instructions.');
        }

        this.initialized = true;
        this.checkSession();
    }

    /**
     * Load user profile from Supabase session
     */
    async loadUserFromSession(session) {
        const { user: authUser } = session;

        // Get profile from database
        let profile = null;
        if (this.supabase) {
            const { data } = await this.supabase
                .from('profiles')
                .select('*')
                .eq('id', authUser.id)
                .single();
            profile = data;
        }

        this.user = {
            email: authUser.email,
            id: authUser.id,
            status: 'active',
            subscription: {
                tier: profile?.subscription_tier || 'pro', // Default to pro for trial
                plan: SUBSCRIPTION_TIERS[profile?.subscription_tier || 'pro'].displayName,
                expiry: profile?.subscription_expires_at || this.getTrialExpiry(),
                isActive: true,
                isTrial: !profile?.subscription_expires_at,
                trialDaysLeft: 7,
                aiRequestsUsed: profile?.ai_requests_used || 0,
                aiRequestsLimit: SUBSCRIPTION_TIERS[profile?.subscription_tier || 'pro'].aiRequests
            }
        };

        saveToStorage('uce_session', this.user);
        this.checkExpirationWarning();
    }

    /**
     * Get trial expiry date (7 days from now)
     */
    getTrialExpiry() {
        const expiry = new Date();
        expiry.setDate(expiry.getDate() + 7);
        return expiry.toISOString().split('T')[0];
    }

    /**
     * Register new user
     */
    async register(email, password, fullName = '') {
        if (this.supabase) {
            const { data, error } = await this.supabase.auth.signUp({
                email,
                password,
                options: {
                    data: { full_name: fullName }
                }
            });

            if (error) {
                return { success: false, error: error.message };
            }

            return {
                success: true,
                message: 'Kayıt başarılı! E-posta adresinizi doğrulayın.',
                user: data.user
            };
        }

        // Fallback to mock registration
        return this.login(email, password);
    }

    async login(email, password) {
        console.log(`Login attempt for: ${email}`);

        // Use Supabase if available
        if (this.supabase) {
            const { data, error } = await this.supabase.auth.signInWithPassword({
                email,
                password
            });

            if (error) {
                return { success: false, error: error.message };
            }

            await this.loadUserFromSession(data.session);
            return { success: true, user: this.user };
        }

        // Mock login for development
        if (email && password) {
            let tier = 'pro';
            let expiry = new Date();
            expiry.setFullYear(expiry.getFullYear() + 1);

            let isTrial = email.toLowerCase().includes('trial');
            if (isTrial) {
                tier = 'pro';
                expiry = new Date();
                expiry.setDate(expiry.getDate() + 7);
            }

            this.user = {
                email,
                id: 'user_' + btoa(email).substring(0, 8),
                status: 'active',
                subscription: {
                    tier: tier,
                    plan: SUBSCRIPTION_TIERS[tier].displayName,
                    expiry: expiry.toISOString().split('T')[0],
                    isActive: true,
                    isTrial: isTrial,
                    trialDaysLeft: isTrial ? 7 : 0,
                    aiRequestsUsed: 0,
                    aiRequestsLimit: SUBSCRIPTION_TIERS[tier].aiRequests
                }
            };
            saveToStorage('uce_session', this.user);
            this.checkExpirationWarning();
            return { success: true, user: this.user };
        }
        return { success: false, error: 'Geçersiz e-posta veya şifre' };
    }

    async checkSubscription() {
        if (!this.user) return false;

        // Mock check - In production, this would query the 'licenses' table in Supabase
        const now = new Date();
        const expiry = new Date(this.user.subscription.expiry);

        if (expiry < now) {
            this.user.subscription.isActive = false;
            this.user.subscription.tier = 'free';
            saveToStorage('uce_session', this.user);
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

        // Enterprise has all features
        if (tierConfig.features.includes('all')) return true;

        return tierConfig.features.includes(featureName);
    }

    /**
     * Check if a specific feature is available
     */
    canUseFeature(featureName) {
        if (!this.user) {
            return { allowed: false, reason: 'Giriş yapmanız gerekiyor' };
        }

        if (!this.user.subscription.isActive) {
            return { allowed: false, reason: 'Aboneliğiniz sona ermiş' };
        }

        if (!this.hasFeature(featureName)) {
            const tierConfig = SUBSCRIPTION_TIERS[this.user.subscription.tier];
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
        const tierConfig = SUBSCRIPTION_TIERS[tier];
        const limit = tierConfig.aiRequests;

        if (limit === -1) return Infinity; // Unlimited

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
        saveToStorage('uce_session', this.user);
        return true;
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

    async updateSubscriptionTier(newTier) {
        if (!SUBSCRIPTION_TIERS[newTier]) {
            console.error(`Invalid tier: ${newTier}`);
            return { success: false, error: 'Geçersiz paket' };
        }

        console.log(`Updating subscription to: ${newTier}`);

        // Update local session
        if (this.user) {
            this.user.subscription.tier = newTier;
            this.user.subscription.plan = SUBSCRIPTION_TIERS[newTier].displayName;
            this.user.subscription.isActive = true;

            // Set expiry date (1 year from now for simplicity)
            const expiry = new Date();
            expiry.setFullYear(expiry.getFullYear() + 1);
            this.user.subscription.expiry = expiry.toISOString().split('T')[0];
            this.user.subscription.isTrial = false;
            this.user.subscription.aiRequestsLimit = SUBSCRIPTION_TIERS[newTier].aiRequests;

            saveToStorage('uce_session', this.user);
        }

        // Update Supabase if connected
        if (this.supabase && this.user) {
            try {
                const { error } = await this.supabase
                    .from('profiles')
                    .update({
                        subscription_tier: newTier,
                        subscription_expires_at: this.user.subscription.expiry
                    })
                    .eq('id', this.user.id);

                if (error) throw error;
            } catch (error) {
                console.error('Supabase update error:', error);
                // We still returned success because local state is updated
            }
        }

        return { success: true, tier: newTier };
    }


    logout() {
        this.user = null;
        removeFromStorage('uce_session');
        window.location.reload();
    }

    checkSession() {
        const session = loadFromStorage('uce_session', null);
        if (session) {
            this.user = session;
            // Recheck subscription status
            this.checkSubscription();
            return true;
        }
        return false;
    }

    isAuthenticated() {
        return this.user !== null || this.checkSession();
    }
}

// Create global instance
window.uceAuth = new UceAuth();

// Export tier definitions for use in other files
window.SUBSCRIPTION_TIERS = SUBSCRIPTION_TIERS;

// Helper function to show upgrade modal
window.showUpgradeModal = function (featureName) {
    const message = `
        <div class="upgrade-prompt">
            <h3>🔒 Özellik Kilitli</h3>
            <p>"${featureName}" özelliği Pro ve üzeri planlarda kullanılabilir.</p>
            <div class="tier-comparison mt-md">
                <div class="tier-card free">
                    <h4>Ücretsiz</h4>
                    <ul>
                        <li>3 Strateji</li>
                        <li>5 Sembol</li>
                        <li>10 AI İstek/Ay</li>
                    </ul>
                </div>
                <div class="tier-card pro recommended">
                    <h4>⭐ Pro</h4>
                    <ul>
                        <li>20 Strateji</li>
                        <li>30 Sembol</li>
                        <li>500 AI İstek/Ay</li>
                        <li>Canlı Trading</li>
                        <li>Confluence Radar</li>
                        <li>Prop Firm Kuralları</li>
                    </ul>
                </div>
            </div>
            <button class="btn btn-primary mt-md" onclick="window.location.href='#pricing'">
                Planı Yükselt
            </button>
        </div>
    `;

    // Use existing toast or modal system
    if (typeof showToast === 'function') {
        showToast(message, 'info', 10000);
    } else {
        alert(`"${featureName}" özelliği Pro ve üzeri planlarda kullanılabilir.`);
    }
};
