/**
 * Services Index - Export all services
 */

import supabaseService from './supabase-service.js';
import updateService from './update-service.js';
import mt5Service from './mt5-service.js';

// Initialize services
async function initializeServices() {
    console.log('[Services] Initializing...');

    // Initialize Supabase first (auth)
    await supabaseService.init();

    // Initialize update checker
    await updateService.init();

    // MT5 connection will be initialized on demand
    console.log('[Services] All services initialized');
}

export {
    supabaseService,
    updateService,
    mt5Service,
    initializeServices
};

// Auto-initialize when DOM is ready
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeServices().catch(console.error);
    });
}
