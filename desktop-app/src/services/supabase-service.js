/**
 * Supabase Service - Authentication & User Data
 * Central service for all Supabase operations
 */

const SUPABASE_URL = 'https://eksixzptfnmfvjdigeiy.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVrc2l4enB0Zm5tZnZqZGlnZWl5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU5OTgzNDIsImV4cCI6MjA1MTU3NDM0Mn0.8N3z9gPJvzJlWf6TqPJRpKSKcHOXbVSU_kFLxIgQyjs';

class SupabaseService {
    constructor() {
        this.client = null;
        this.user = null;
        this.initialized = false;
    }

    /**
     * Initialize Supabase client
     */
    async init() {
        if (this.initialized) return;

        try {
            // Check if Supabase JS is loaded
            if (typeof window !== 'undefined' && window.supabase) {
                this.client = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
                this.initialized = true;
                console.log('[SupabaseService] Initialized successfully');

                // Check for existing session
                const { data: { session } } = await this.client.auth.getSession();
                if (session) {
                    this.user = session.user;
                    await this.loadUserProfile();
                }

                // Listen for auth changes
                this.client.auth.onAuthStateChange(async (event, session) => {
                    if (event === 'SIGNED_IN' && session) {
                        this.user = session.user;
                        await this.loadUserProfile();
                    } else if (event === 'SIGNED_OUT') {
                        this.user = null;
                    }
                });
            } else {
                console.warn('[SupabaseService] Supabase JS not loaded');
            }
        } catch (error) {
            console.error('[SupabaseService] Init failed:', error);
        }
    }

    /**
     * Login with email and password
     */
    async login(email, password) {
        if (!this.client) {
            return { success: false, error: 'Supabase not initialized' };
        }

        try {
            const { data, error } = await this.client.auth.signInWithPassword({
                email,
                password
            });

            if (error) {
                return { success: false, error: error.message };
            }

            this.user = data.user;
            await this.loadUserProfile();
            return { success: true, user: this.user };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Register new user
     */
    async register(email, password, fullName = '') {
        if (!this.client) {
            return { success: false, error: 'Supabase not initialized' };
        }

        try {
            const { data, error } = await this.client.auth.signUp({
                email,
                password,
                options: {
                    data: {
                        full_name: fullName,
                        subscription_tier: 'free'
                    }
                }
            });

            if (error) {
                return { success: false, error: error.message };
            }

            return {
                success: true,
                user: data.user,
                message: 'E-posta adresinize doğrulama linki gönderildi.'
            };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Logout
     */
    async logout() {
        if (!this.client) return;
        await this.client.auth.signOut();
        this.user = null;
    }

    /**
     * Load user profile from database
     */
    async loadUserProfile() {
        if (!this.client || !this.user) return;

        try {
            const { data, error } = await this.client
                .from('user_profiles')
                .select('*')
                .eq('user_id', this.user.id)
                .single();

            if (data) {
                this.user.profile = data;
            }
        } catch (error) {
            console.warn('[SupabaseService] Could not load profile:', error);
        }
    }

    /**
     * Get current user
     */
    getUser() {
        return this.user;
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.user;
    }

    /**
     * Get subscription tier
     */
    getSubscriptionTier() {
        if (!this.user) return 'free';
        return this.user.profile?.subscription_tier ||
            this.user.user_metadata?.subscription_tier ||
            'free';
    }

    /**
     * Check if user has specific feature access
     */
    hasFeature(featureName) {
        const tier = this.getSubscriptionTier();
        const tierFeatures = {
            free: ['dashboard', 'basic_analysis'],
            pro: ['dashboard', 'basic_analysis', 'advanced_backtest', 'telegram', 'ai_unlimited'],
            elite: ['dashboard', 'basic_analysis', 'advanced_backtest', 'telegram', 'ai_unlimited', 'priority_support', 'custom_strategies']
        };
        return tierFeatures[tier]?.includes(featureName) || false;
    }
}

// Export singleton
const supabaseService = new SupabaseService();
export default supabaseService;

// Also expose globally for non-module scripts
if (typeof window !== 'undefined') {
    window.supabaseService = supabaseService;
}
