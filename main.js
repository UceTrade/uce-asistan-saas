/**
 * UceAsistan - Main Application Entry Point
 * Centralized script initialization and module management
 * 
 * This file coordinates all JavaScript modules and provides
 * a clean entry point for the application.
 */

(function () {
    'use strict';

    // Application version
    const APP_VERSION = '3.0.0';
    const DEBUG = localStorage.getItem('uce_debug') === 'true';

    // Module registry - tracks which modules have been initialized
    const modules = {
        auth: false,
        mt5Connector: false,
        riskManager: false,
        aiEngine: false,
        dashboard: false,
        backtest: false,
        journal: false,
        marketTerminal: false,
        strategies: false,
        enhancedFeatures: false
    };

    /**
     * Logger utility with debug mode support
     */
    const logger = {
        info: (msg, ...args) => {
            console.log(`[UceAsistan] ${msg}`, ...args);
        },
        debug: (msg, ...args) => {
            if (DEBUG) console.log(`[DEBUG] ${msg}`, ...args);
        },
        error: (msg, ...args) => {
            console.error(`[ERROR] ${msg}`, ...args);
        },
        warn: (msg, ...args) => {
            console.warn(`[WARN] ${msg}`, ...args);
        }
    };

    /**
     * Performance monitoring
     */
    const perf = {
        marks: new Map(),
        start: (label) => {
            perf.marks.set(label, performance.now());
        },
        end: (label) => {
            const start = perf.marks.get(label);
            if (start) {
                const duration = performance.now() - start;
                logger.debug(`${label}: ${duration.toFixed(2)}ms`);
                perf.marks.delete(label);
                return duration;
            }
            return 0;
        }
    };

    /**
     * Module registration and initialization tracking
     */
    function registerModule(name) {
        if (modules.hasOwnProperty(name)) {
            modules[name] = true;
            logger.debug(`Module registered: ${name}`);
        }
    }

    function isModuleReady(name) {
        return modules[name] === true;
    }

    function getAllModuleStatus() {
        return { ...modules };
    }

    /**
     * Event bus for inter-module communication
     */
    const eventBus = {
        _events: new Map(),

        on: function (event, callback) {
            if (!this._events.has(event)) {
                this._events.set(event, []);
            }
            this._events.get(event).push(callback);
        },

        off: function (event, callback) {
            if (this._events.has(event)) {
                const callbacks = this._events.get(event);
                const index = callbacks.indexOf(callback);
                if (index > -1) callbacks.splice(index, 1);
            }
        },

        emit: function (event, data) {
            if (this._events.has(event)) {
                this._events.get(event).forEach(cb => {
                    try {
                        cb(data);
                    } catch (e) {
                        logger.error(`Event handler error for ${event}:`, e);
                    }
                });
            }
        }
    };

    /**
     * Settings manager - centralized configuration
     */
    const settings = {
        _cache: null,

        defaults: {
            theme: 'dark',
            language: 'tr',
            refreshInterval: 1000,
            maxDrawdown: 10,
            dailyLossLimit: 500,
            aiProvider: 'groq',
            notifications: true
        },

        get: function (key) {
            if (!this._cache) {
                this._cache = JSON.parse(localStorage.getItem('uce_settings') || '{}');
            }
            return this._cache[key] ?? this.defaults[key];
        },

        set: function (key, value) {
            if (!this._cache) {
                this._cache = JSON.parse(localStorage.getItem('uce_settings') || '{}');
            }
            this._cache[key] = value;
            localStorage.setItem('uce_settings', JSON.stringify(this._cache));
            eventBus.emit('settings:changed', { key, value });
        },

        getAll: function () {
            return { ...this.defaults, ...this._cache };
        },

        reset: function () {
            this._cache = {};
            localStorage.removeItem('uce_settings');
        }
    };

    /**
     * Feature flags for gradual rollouts
     */
    const features = {
        _flags: {
            newTerminal: true,
            aiEditor: true,
            confluence: true,
            mtfAnalysis: true,
            recoveryPlan: true,
            cryptoPayments: true
        },

        isEnabled: function (flag) {
            return this._flags[flag] === true;
        },

        enable: function (flag) {
            this._flags[flag] = true;
        },

        disable: function (flag) {
            this._flags[flag] = false;
        }
    };

    /**
     * Initialize application on DOM ready
     */
    function onDOMReady(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    }

    // Expose to global scope
    window.UceAsistan = {
        version: APP_VERSION,
        debug: DEBUG,
        logger,
        perf,
        eventBus,
        settings,
        features,
        registerModule,
        isModuleReady,
        getAllModuleStatus,
        onDOMReady
    };

    // Log application start
    logger.info(`UceAsistan v${APP_VERSION} initialized`);
    if (DEBUG) logger.debug('Debug mode enabled');

})();
