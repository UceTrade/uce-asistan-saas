/**
 * MT5 Service - Local backend communication
 * Handles WebSocket connection to local Python server
 */

const LOCAL_WS_URL = 'ws://localhost:8766';

class MT5Service {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.handlers = new Map();
        this.eventListeners = new Map();
        this.pendingRequests = new Map();
        this.requestId = 0;
    }

    /**
     * Connect to local Python server
     */
    async connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(LOCAL_WS_URL);

                this.ws.onopen = () => {
                    this.connected = true;
                    this.reconnectAttempts = 0;
                    console.log('[MT5Service] Connected to local server');
                    this.emit('connected');
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event.data);
                };

                this.ws.onerror = (error) => {
                    console.error('[MT5Service] WebSocket error:', error);
                    this.emit('error', error);
                };

                this.ws.onclose = () => {
                    this.connected = false;
                    console.log('[MT5Service] Connection closed');
                    this.emit('disconnected');
                    this.attemptReconnect();
                };

                // Timeout after 10 seconds
                setTimeout(() => {
                    if (!this.connected) {
                        reject(new Error('Connection timeout'));
                    }
                }, 10000);

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Disconnect from server
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
            this.connected = false;
        }
    }

    /**
     * Attempt to reconnect
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('[MT5Service] Max reconnect attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

        console.log(`[MT5Service] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            this.connect().catch(err => {
                console.error('[MT5Service] Reconnect failed:', err);
            });
        }, delay);
    }

    /**
     * Send message to server
     */
    send(action, data = {}) {
        if (!this.connected || !this.ws) {
            console.warn('[MT5Service] Not connected');
            return false;
        }

        const message = JSON.stringify({ action, ...data });
        this.ws.send(message);
        return true;
    }

    /**
     * Send message and wait for response
     */
    async sendAndWait(action, data = {}, timeout = 30000) {
        return new Promise((resolve, reject) => {
            const requestId = ++this.requestId;

            const timeoutId = setTimeout(() => {
                this.pendingRequests.delete(requestId);
                reject(new Error('Request timeout'));
            }, timeout);

            this.pendingRequests.set(requestId, { resolve, reject, timeoutId });

            this.send(action, { ...data, request_id: requestId });
        });
    }

    /**
     * Handle incoming message
     */
    handleMessage(rawData) {
        try {
            const data = JSON.parse(rawData);

            // Check for pending request response
            if (data.request_id && this.pendingRequests.has(data.request_id)) {
                const { resolve, timeoutId } = this.pendingRequests.get(data.request_id);
                clearTimeout(timeoutId);
                this.pendingRequests.delete(data.request_id);
                resolve(data);
                return;
            }

            // Emit to type-specific handlers
            if (data.type && this.handlers.has(data.type)) {
                this.handlers.get(data.type).forEach(handler => handler(data));
            }

            // Emit general message event
            this.emit('message', data);

        } catch (error) {
            console.error('[MT5Service] Message parse error:', error);
        }
    }

    /**
     * Register handler for message type
     */
    on(type, handler) {
        if (!this.handlers.has(type)) {
            this.handlers.set(type, []);
        }
        this.handlers.get(type).push(handler);
    }

    /**
     * Register event listener
     */
    addEventListener(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    /**
     * Emit event
     */
    emit(event, data = null) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => callback(data));
        }
    }

    /**
     * Get account data
     */
    async getAccountData() {
        return this.sendAndWait('get_account_data');
    }

    /**
     * Get market analysis
     */
    async getMarketAnalysis(symbol) {
        return this.sendAndWait('get_market_analysis', { symbol });
    }

    /**
     * Run backtest
     */
    async runBacktest(params) {
        return this.sendAndWait('run_backtest', params, 120000);
    }

    /**
     * Start live trading
     */
    async startLiveTrading(params) {
        return this.sendAndWait('start_live_trading', params);
    }

    /**
     * Stop live trading
     */
    async stopLiveTrading() {
        return this.sendAndWait('stop_live_trading');
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.connected;
    }
}

// Export singleton
const mt5Service = new MT5Service();
export default mt5Service;

// Also expose globally
if (typeof window !== 'undefined') {
    window.mt5Service = mt5Service;
}
