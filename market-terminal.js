/**
 * Market Terminal - Bloomberg-style market data terminal
 * Kullanıcı ham verileri görüp kendi yorumunu yapar
 */

class MarketTerminal {
    constructor() {
        this.refreshInterval = null;
        this.marketData = {};
        this.symbols = {
            majorFX: ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD'],
            metalsCrypto: ['XAUUSD', 'XAGUSD', 'BTCUSD', 'ETHUSD'],
            indices: ['US30', 'SPX500', 'NAS100', 'GER40']
        };
        this.allSymbols = [...this.symbols.majorFX, ...this.symbols.metalsCrypto, ...this.symbols.indices];
    }

    init() {
        console.log('[TERMINAL] Market Terminal initialized');
        this.startClock();
        this.updateSessionStatus();

        // Initial data load after 1 second
        setTimeout(() => {
            this.refreshAll();
        }, 1000);

        // Update sessions every minute
        setInterval(() => {
            this.updateSessionStatus();
        }, 60000);
    }

    /**
     * Start realtime clock
     */
    startClock() {
        const updateTime = () => {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            const timeEl = document.getElementById('terminalTime');
            if (timeEl) timeEl.textContent = timeStr;
        };

        updateTime();
        setInterval(updateTime, 1000);
    }

    /**
     * Set auto-refresh rate
     */
    setRefreshRate(seconds) {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }

        if (seconds > 0) {
            console.log(`[TERMINAL] Auto-refresh: ${seconds}s`);
            this.refreshInterval = setInterval(() => {
                this.refreshAll();
            }, seconds * 1000);
        }
    }

    /**
     * Refresh all market data
     */
    async refreshAll() {
        console.log('[TERMINAL] Refreshing market data from Yahoo Finance...');

        this.setMarketStatus('loading');

        try {
            // Check if WebSocket is connected
            if (!window.mt5Connector) {
                console.warn('[TERMINAL] mt5Connector not available yet');
                this.setMarketStatus('offline');
                return;
            }

            if (!window.mt5Connector.connected) {
                console.warn('[TERMINAL] WebSocket not connected, waiting...');
                // Try again in 2 seconds
                setTimeout(() => this.refreshAll(), 2000);
                return;
            }

            // Request all Yahoo data in one call
            console.log('[TERMINAL] Sending get_yahoo_all request...');
            const response = await window.mt5Connector.sendMessage({
                action: 'get_yahoo_all'
            });

            console.log('[TERMINAL] Response received:', response);

            // Handle response - check for wrapped (response.data) or direct data format
            if (response && !response.error) {
                // Check if data is wrapped in 'data' property or directly contains symbols
                if (response.data && typeof response.data === 'object') {
                    // Wrapped format: { data: { EURUSD: {...}, ... } }
                    this.marketData = response.data;
                    console.log('[TERMINAL] Yahoo Finance data received (wrapped):', Object.keys(this.marketData).length, 'symbols');
                } else if (response.EURUSD || response.GBPUSD || response.BTCUSD) {
                    // Direct format: { EURUSD: {...}, GBPUSD: {...}, ... }
                    this.marketData = response;
                    console.log('[TERMINAL] Yahoo Finance data received (direct):', Object.keys(this.marketData).length, 'symbols');
                } else {
                    console.warn('[TERMINAL] Unknown response format, trying individual requests');
                    await this.fetchIndividualSymbols();
                }
            } else if (response && response.error) {
                console.error('[TERMINAL] Yahoo API error:', response.error);
                await this.fetchIndividualSymbols();
            } else {
                console.warn('[TERMINAL] Empty response, trying individual requests');
                await this.fetchIndividualSymbols();
            }

            // Update UI
            this.updatePanels();
            this.updateTicker();
            this.updateMovers();
            this.updateStats();
            this.setMarketStatus('online');

        } catch (error) {
            console.error('[TERMINAL] Refresh failed:', error);
            this.setMarketStatus('offline');
        }
    }

    /**
     * Fetch individual symbols one by one (fallback)
     */
    async fetchIndividualSymbols() {
        console.log('[TERMINAL] Fetching individual symbols...');
        const promises = this.allSymbols.map(symbol => this.getSymbolData(symbol));
        const results = await Promise.allSettled(promises);

        results.forEach((result, index) => {
            if (result.status === 'fulfilled' && result.value && !result.value.error) {
                this.marketData[this.allSymbols[index]] = result.value;
            }
        });
        console.log('[TERMINAL] Individual fetch complete:', Object.keys(this.marketData).length, 'symbols');
    }

    /**
     * Get data for single symbol (Yahoo Finance)
     */
    async getSymbolData(symbol) {
        if (!window.mt5Connector || !window.mt5Connector.connected) {
            return null;
        }

        try {
            const response = await window.mt5Connector.sendMessage({
                action: 'get_yahoo_quote',
                symbol: symbol
            });

            return response;
        } catch (e) {
            console.warn(`[TERMINAL] Failed to get ${symbol}:`, e.message);
            return null;
        }
    }

    /**
     * Update watchlist panels
     */
    updatePanels() {
        this.renderPanel('panelMajorFX', this.symbols.majorFX);
        this.renderPanel('panelMetalsCrypto', this.symbols.metalsCrypto);
        this.renderPanel('panelIndices', this.symbols.indices);
    }

    /**
     * Render a single panel
     */
    renderPanel(panelId, symbols) {
        const panel = document.getElementById(panelId);
        if (!panel) return;

        let html = '';

        symbols.forEach(symbol => {
            const data = this.marketData[symbol];
            if (!data || data.error) {
                html += this.createWatchlistItem(symbol, null);
            } else {
                html += this.createWatchlistItem(symbol, data);
            }
        });

        panel.innerHTML = html || '<div class="watchlist-empty">Veri yok</div>';
    }

    /**
     * Create watchlist item HTML
     */
    createWatchlistItem(symbol, data) {
        if (!data) {
            return `
                <div class="watchlist-item offline" onclick="window.marketTerminal.showDetail('${symbol}')">
                    <span class="wl-symbol">${symbol}</span>
                    <span class="wl-price">--</span>
                    <span class="wl-change">N/A</span>
                </div>
            `;
        }

        const price = data.price ? data.price.toFixed(data.price > 100 ? 2 : 5) : '--';
        const change = data.change_24h || 0;
        const changeClass = change >= 0 ? 'positive' : 'negative';
        const changeArrow = change >= 0 ? '▲' : '▼';
        const trend = data.trend || 'neutral';

        return `
            <div class="watchlist-item ${trend}" onclick="window.marketTerminal.showDetail('${symbol}')">
                <div class="wl-left">
                    <span class="wl-symbol">${symbol}</span>
                    <span class="wl-trend trend-${trend}">${this.getTrendIcon(trend)}</span>
                </div>
                <div class="wl-right">
                    <span class="wl-price">${price}</span>
                    <span class="wl-change ${changeClass}">${changeArrow} ${Math.abs(change).toFixed(2)}%</span>
                </div>
            </div>
        `;
    }

    /**
     * Get trend icon
     */
    getTrendIcon(trend) {
        if (trend === 'uptrend') return '📈';
        if (trend === 'downtrend') return '📉';
        return '➡️';
    }

    /**
     * Update top ticker bar
     */
    updateTicker() {
        const ticker = document.getElementById('tickerScroll');
        if (!ticker) return;

        let html = '';

        Object.entries(this.marketData).forEach(([symbol, data]) => {
            if (!data || data.error) return;

            const change = data.change_24h || 0;
            const changeClass = change >= 0 ? 'positive' : 'negative';
            const price = data.price ? data.price.toFixed(data.price > 100 ? 2 : 5) : '--';

            html += `
                <span class="ticker-item ${changeClass}">
                    <span class="ticker-symbol">${symbol}</span>
                    <span class="ticker-price">${price}</span>
                    <span class="ticker-change">${change >= 0 ? '+' : ''}${change.toFixed(2)}%</span>
                </span>
            `;
        });

        // Duplicate for seamless scroll
        ticker.innerHTML = html + html || '<span class="ticker-item">Veri bekleniyor...</span>';
    }

    /**
     * Update market movers (top gainers/losers)
     */
    updateMovers() {
        const allData = Object.entries(this.marketData)
            .filter(([_, data]) => data && !data.error && data.change_24h !== undefined)
            .map(([symbol, data]) => ({ symbol, change: data.change_24h }))
            .sort((a, b) => b.change - a.change);

        const gainers = allData.slice(0, 3);
        const losers = allData.slice(-3).reverse();

        const gainersEl = document.getElementById('topGainers');
        const losersEl = document.getElementById('topLosers');

        if (gainersEl) {
            gainersEl.innerHTML = gainers.map(g =>
                `<div class="mover-item"><span>${g.symbol}</span><span class="text-success">+${g.change.toFixed(2)}%</span></div>`
            ).join('') || '--';
        }

        if (losersEl) {
            losersEl.innerHTML = losers.map(l =>
                `<div class="mover-item"><span>${l.symbol}</span><span class="text-danger">${l.change.toFixed(2)}%</span></div>`
            ).join('') || '--';
        }
    }

    /**
     * Update session status
     */
    updateSessionStatus() {
        const now = new Date();
        const utcHour = now.getUTCHours();

        // Tokyo: 00:00 - 09:00 UTC
        this.setSessionActive('sessionTokyo', utcHour >= 0 && utcHour < 9);

        // London: 07:00 - 16:00 UTC  
        this.setSessionActive('sessionLondon', utcHour >= 7 && utcHour < 16);

        // New York: 12:00 - 21:00 UTC
        this.setSessionActive('sessionNewYork', utcHour >= 12 && utcHour < 21);
    }

    /**
     * Set session active/inactive
     */
    setSessionActive(sessionId, isActive) {
        const row = document.getElementById(sessionId);
        if (!row) return;

        const status = row.querySelector('.session-status');
        if (status) {
            status.className = `session-status ${isActive ? 'open' : 'closed'}`;
            status.textContent = isActive ? 'AÇIK' : 'KAPALI';
        }
    }

    /**
     * Update stats panel
     */
    updateStats() {
        const activeCount = Object.values(this.marketData).filter(d => d && !d.error).length;
        const now = new Date();

        document.getElementById('statActiveSymbols').textContent = activeCount;
        document.getElementById('statLastUpdate').textContent = now.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });

        // DXY (US Dollar Index)
        const dxy = this.marketData['DXY'];
        if (dxy && dxy.price && !dxy.error) {
            const dxyEl = document.getElementById('statDXY');
            if (dxyEl) {
                dxyEl.textContent = dxy.price.toFixed(2);
                dxyEl.className = `stat-value ${dxy.change_24h >= 0 ? 'text-success' : 'text-danger'}`;
            }
        }

        // VIX (Fear Index)
        const vix = this.marketData['VIX'];
        if (vix && vix.price && !vix.error) {
            const vixEl = document.getElementById('statVIX');
            if (vixEl) {
                vixEl.textContent = vix.price.toFixed(2);
                // VIX: high = fear (red), low = calm (green)
                vixEl.className = `stat-value ${vix.price < 20 ? 'text-success' : vix.price > 30 ? 'text-danger' : 'text-warning'}`;
            }
        }
    }

    /**
     * Set market status indicator
     */
    setMarketStatus(status) {
        const statusEl = document.getElementById('marketStatus');
        if (!statusEl) return;

        statusEl.className = `market-status ${status}`;

        const statusText = statusEl.querySelector('.status-text');
        if (statusText) {
            switch (status) {
                case 'online': statusText.textContent = 'ONLINE'; break;
                case 'loading': statusText.textContent = 'LOADING...'; break;
                case 'offline': statusText.textContent = 'OFFLINE'; break;
                default: statusText.textContent = 'UNKNOWN';
            }
        }
    }

    /**
     * Show symbol detail modal
     */
    showDetail(symbol) {
        const modal = document.getElementById('symbolDetailModal');
        const data = this.marketData[symbol];

        if (!modal) return;

        document.getElementById('detailSymbolName').textContent = symbol;

        if (data && !data.error) {
            const price = data.price ? data.price.toFixed(data.price > 100 ? 2 : 5) : '--';
            const change = data.change_24h || 0;
            const changeClass = change >= 0 ? 'positive' : 'negative';

            document.getElementById('detailPrice').textContent = price;
            document.getElementById('detailChange').textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            document.getElementById('detailChange').className = `detail-change ${changeClass}`;

            // Set OHLC if available
            document.getElementById('detailOpen').textContent = '--';
            document.getElementById('detailHigh').textContent = '--';
            document.getElementById('detailLow').textContent = '--';
            document.getElementById('detailSpread').textContent = '--';
        }

        modal.classList.remove('hidden');

        // Store current symbol for trade actions
        this.currentDetailSymbol = symbol;
    }

    /**
     * Close detail modal
     */
    closeDetail() {
        const modal = document.getElementById('symbolDetailModal');
        if (modal) modal.classList.add('hidden');
    }
}

// Create global instance
window.marketTerminal = new MarketTerminal();

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for MT5 connection
    setTimeout(() => {
        window.marketTerminal.init();
    }, 2000);
});

// Also try to init when view is switched
const originalSwitchView = window.switchView;
if (originalSwitchView) {
    window.switchView = function (view) {
        originalSwitchView(view);
        if (view === 'neural' && window.marketTerminal) {
            window.marketTerminal.refreshAll();
        }
    };
}
