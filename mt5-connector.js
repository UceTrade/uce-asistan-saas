/**
 * MT5 Connector - WebSocket client for MT5 backend communication
 */

class MT5Connector {
    constructor() {
        // Detect Deployment Mode
        this.isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

        // Both Production and Development connect to the local backend
        // The backend always runs on port 8766
        this.url = 'ws://localhost:8766';

        console.log(`[MT5Connector] Environment: ${this.isProduction ? 'PRODUCTION' : 'DEVELOPMENT'}`);
        console.log(`[MT5Connector] Targeted Bridge: ${this.url}`);

        this.ws = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.messageHandlers = new Map();
        this.eventListeners = new Map();
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);

                this.ws.onopen = () => {
                    console.log('MT5 sunucusuna bağlanıldı');
                    this.connected = true;
                    this.reconnectAttempts = 0;
                    this.updateConnectionStatus(true);
                    this.emit('connected');
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event.data);
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket hatası:', error);
                    this.emit('error', error);
                };

                this.ws.onclose = () => {
                    console.log('MT5 sunucusu bağlantısı kesildi');
                    this.connected = false;
                    this.updateConnectionStatus(false);
                    this.emit('disconnected');
                    this.attemptReconnect();
                };

            } catch (error) {
                console.error('Bağlantı hatası:', error);
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
            console.error('Maksimum yeniden bağlanma denemesine ulaşıldı');
            showError('MT5 sunucusuna bağlanılamadı. Lütfen sunucunun çalıştığından emin olun.');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`${delay}ms içinde yeniden bağlanılıyor... (Deneme ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            this.connect().catch(err => {
                console.error('Yeniden bağlanma başarısız:', err);
            });
        }, delay);
    }

    /**
     * Send message to server
     */
    send(data) {
        if (!this.connected || !this.ws) {
            console.error('Sunucuya bağlı değil');
            return false;
        }

        try {
            this.ws.send(JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Mesaj gönderilemedi:', error);
            return false;
        }
    }

    /**
     * Handle incoming message
     */
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            const type = message.type;

            // Emit event for this message type
            this.emit(type, message.data || message);

            // Call registered handler if exists
            if (this.messageHandlers.has(type)) {
                this.messageHandlers.get(type)(message.data || message);
            }

        } catch (error) {
            console.error('Mesaj işlenemedi:', error);
        }
    }

    /**
     * Register message handler
     */
    on(type, handler) {
        this.messageHandlers.set(type, handler);
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
    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                callback(data);
            });
        }
    }

    /**
     * Update connection status in UI
     */
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        const indicatorElement = document.getElementById('statusIndicator');
        const messageElement = document.getElementById('statusMessage');

        if (statusElement) {
            statusElement.style.display = 'block';
        }

        if (indicatorElement && messageElement) {
            if (connected) {
                indicatorElement.className = 'badge badge-success';
                indicatorElement.textContent = '🟢 Bağlandı';
                messageElement.textContent = 'MT5 sunucusuna bağlanıldı';

                // Hide after 3 seconds
                setTimeout(() => {
                    if (statusElement) {
                        statusElement.style.display = 'none';
                    }
                }, 3000);
            } else {
                indicatorElement.className = 'badge badge-danger';
                indicatorElement.textContent = '🔴 Bağlantı Kesildi';
                messageElement.textContent = 'Yeniden bağlanmaya çalışılıyor...';
            }
        }
    }

    // ============================================
    // API METHODS
    // ============================================

    /**
     * Add MT5 account
     */
    addAccount(accountId, login, password, server) {
        return this.send({
            action: 'add_account',
            account_id: accountId,
            login: parseInt(login),
            password: password,
            server: server
        });
    }

    /**
     * Remove MT5 account
     */
    removeAccount(accountId) {
        return this.send({
            action: 'remove_account',
            account_id: accountId
        });
    }

    /**
     * Get account data
     */
    getAccountData(accountId) {
        return this.send({
            action: 'get_account_data',
            account_id: accountId
        });
    }

    /**
     * Get portfolio summary
     */
    getPortfolio() {
        return this.send({
            action: 'get_portfolio'
        });
    }

    /**
     * Get risk metrics
     */
    getRiskMetrics(accountId, maxDrawdown = 10.0, dailyLimit = 5.0) {
        return this.send({
            action: 'get_risk_metrics',
            account_id: accountId,
            max_drawdown_pct: maxDrawdown,
            daily_limit_pct: dailyLimit
        });
    }

    /**
     * Get market analysis for symbol
     */
    getMarketAnalysis(symbol) {
        return this.send({
            action: 'get_market_analysis',
            symbol: symbol
        });
    }

    /**
     * Send ping
     */
    ping() {
        return this.send({
            action: 'ping'
        });
    }

    /**
     * Send message and wait for response
     */
    sendMessage(data) {
        return new Promise((resolve, reject) => {
            if (!this.connected) {
                reject(new Error('Sunucuya bağlı değil'));
                return;
            }

            // Set up one-time listener for response
            const responseType = data.action === 'parse_strategy' ? 'strategy_parsed' :
                data.action === 'run_backtest' ? 'backtest_result' :
                    data.action === 'load_template' ? 'template_loaded' :
                        data.action === 'start_conversation' ? 'conversation_question' :
                            data.action === 'answer_question' ? 'conversation_question' :
                                data.action === 'generate_final_prompt' ? 'final_prompt' :
                                    data.action === 'optimize_strategy' ? 'optimization_suggestions' :
                                        data.action === 'optimize_strategy' ? 'optimization_suggestions' :
                                            data.action === 'find_confluences' ? 'confluences_found' :
                                                data.action === 'get_templates' ? 'templates_list' :
                                                    data.action === 'get_strategies' ? 'strategies_list' :
                                                        data.action === 'mtf_analysis' ? 'mtf_analysis_result' :
                                                            data.action === 'get_recovery_plan' ? 'recovery_plan' :
                                                                data.action + '_response';

            // Longer timeout for heavy operations (backtest with pa.analyze_all)
            // Default: 300s for backtest, 120s for strategy parsing, 60s for others
            const defaultTimeout = data.action === 'run_backtest' ? 300000 :  // 5 min
                data.action === 'parse_strategy' ? 120000 : // 2 min
                    data.action === 'evolve_strategy' ? 180000 : // 3 min
                        60000; // 1 min for others

            const timeout = setTimeout(() => {
                this.messageHandlers.delete(responseType);
                reject(new Error('İstek zaman aşımına uğradı'));
            }, data.requestTimeout || defaultTimeout);

            this.on(responseType, (response) => {
                clearTimeout(timeout);
                this.messageHandlers.delete(responseType);
                resolve(response);
            });

            // Send the message
            if (!this.send(data)) {
                clearTimeout(timeout);
                this.messageHandlers.delete(responseType);
                reject(new Error('Mesaj gönderilemedi'));
            }
        });
    }
}

// Create global instance
window.mt5Connector = new MT5Connector();
