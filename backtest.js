/**
 * Backtest Module - AI-powered strategy testing
 */

class Backtest {
    constructor() {
        this.equityCurveChart = null;
        this.currentStrategy = null;
        this.currentTrades = [];  // Store trades for click handler
        this.visibleTrades = 0;   // Performancefix: Number of rendered trades
        this.batchSize = 50;      // Performancefix: Trades per batch
        this.initializeDates();
    }

    /**
     * Initialize default date range (last 30 days)
     */
    initializeDates() {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);

        const formatDate = (date) => {
            return date.toISOString().split('T')[0];
        };

        // Set default dates when page loads
        setTimeout(() => {
            const startInput = document.getElementById('btStartDate');
            const endInput = document.getElementById('btEndDate');

            if (startInput) startInput.value = formatDate(startDate);
            if (endInput) endInput.value = formatDate(endDate);
        }, 100);
    }

    /**
     * Initialize backtest chart
     */
    initBacktestChart() {
        const ctx = document.getElementById('equityCurveChart');
        if (!ctx) return;

        if (this.equityCurveChart) {
            this.equityCurveChart.destroy();
        }

        this.equityCurveChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: '#a0aec0' }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(5);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#a0aec0'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#a0aec0',
                            maxTicksLimit: 10
                        }
                    }
                },
                onClick: (event, elements) => {
                    // Handle click on trade markers
                    if (elements.length > 0) {
                        const element = elements[0];
                        const datasetIndex = element.datasetIndex;
                        const index = element.index;

                        // Only handle clicks on buy/sell datasets (index 1 and 2)
                        if (datasetIndex === 1 || datasetIndex === 2) {
                            this.showTradePopup(index, datasetIndex === 1 ? 'LONG' : 'SHORT');
                        }
                    }
                }
            }
        });
    }

    /**
     * Generate strategy code from description using AI
     */
    async generateStrategy() {
        const description = document.getElementById('strategyDescription').value.trim();

        if (!description) {
            showError('Please describe your trading strategy');
            return;
        }

        // Check if API key is configured
        if (!aiEngine || !aiEngine.apiKey) {
            showError('Please configure AI API key in Settings first');
            openSettingsModal();
            return;
        }

        try {
            showInfo('🤖 Generating strategy code with AI... This may take 10-15 seconds.');

            console.log('Sending strategy generation request...');
            console.log('Provider:', aiEngine.provider);
            console.log('Description:', description);

            // Send to backend
            const response = await mt5Connector.sendMessage({
                action: 'parse_strategy',
                description: description,
                ai_provider: aiEngine.provider,
                api_key: aiEngine.apiKey.trim()  // Trim whitespace
            });

            console.log('Received response:', response);

            if (response && response.success) {
                console.log('Strategy code received:', response.code);

                this.currentStrategy = response.code;
                const codeTextarea = document.getElementById('strategyCode');
                const codeSection = document.getElementById('generatedCodeSection');

                // Handle Summary
                const summarySection = document.getElementById('strategySummarySection');
                const summaryText = document.getElementById('strategySummaryText');

                if (summarySection && summaryText) {
                    if (response.summary && response.summary !== "Özet bulunamadı.") {
                        summaryText.textContent = response.summary;
                        summarySection.style.display = 'block';
                    } else {
                        summarySection.style.display = 'none';
                    }
                }

                if (codeTextarea) {
                    codeTextarea.value = response.code;
                    console.log('Code set to textarea');
                } else {
                    console.error('strategyCode textarea not found!');
                }

                if (codeSection) {
                    codeSection.classList.remove('hidden');
                    codeSection.style.display = 'block';  // Force display
                    console.log('Code section shown');
                } else {
                    console.error('generatedCodeSection not found!');
                }

                showSuccess('✅ Strategy code generated successfully!');

                // Scroll to code section
                setTimeout(() => {
                    if (codeSection) {
                        codeSection.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }, 100);
            } else {
                const errorMsg = response && response.error ? response.error : 'Unknown error occurred';
                console.error('Strategy generation failed:', errorMsg);
                showError('❌ Failed to generate strategy: ' + errorMsg);
            }
        } catch (error) {
            console.error('Error generating strategy:', error);
            showError('❌ Error: ' + error.message + '. Check console for details.');
        }
    }

    /**
     * Show backtest parameters section
     */
    showBacktestParams() {
        console.log('showBacktestParams called');

        const code = document.getElementById('strategyCode').value.trim();
        console.log('Strategy code length:', code.length);

        if (!code) {
            showError('No strategy code to test');
            return;
        }

        this.currentStrategy = code;

        const paramsSection = document.getElementById('backtestParamsSection');
        console.log('Params section element:', paramsSection);

        if (paramsSection) {
            paramsSection.classList.remove('hidden');
            paramsSection.style.display = 'block';  // Force display
            console.log('Params section shown');

            // Scroll to parameters
            setTimeout(() => {
                paramsSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }, 100);
        } else {
            console.error('backtestParamsSection not found!');
        }
    }

    /**
     * Clear strategy and reset form
     */
    clearStrategy() {
        document.getElementById('strategyDescription').value = '';
        document.getElementById('strategyCode').value = '';
        document.getElementById('templateSelector').value = '';
        this.currentStrategy = null;
        hideElement('generatedCodeSection');
        hideElement('backtestParamsSection');
        hideElement('backtestResults');
    }

    /**
     * Load a pre-built strategy template
     */
    async loadTemplate() {
        const templateId = document.getElementById('templateSelector').value;

        if (!templateId) {
            // User selected "start from scratch"
            return;
        }

        try {
            showInfo('📥 Loading template...');

            const response = await mt5Connector.sendMessage({
                action: 'load_template',
                template_id: templateId,
                params: {}
            });

            console.log('[DEBUG] Template response:', response);

            // Response structure: { data: { success: true, code: '...', ... } }
            if (response && response.success) {
                const template = response;

                // Populate description
                document.getElementById('strategyDescription').value = template.description;

                // Populate code
                document.getElementById('strategyCode').value = template.code;
                this.currentStrategy = template.code;

                // Show summary if available
                const summarySection = document.getElementById('strategySummarySection');
                const summaryText = document.getElementById('strategySummaryText');

                if (summarySection && summaryText && template.summary) {
                    summaryText.textContent = template.summary;
                    summarySection.style.display = 'block';
                }

                // Show code section
                const codeSection = document.getElementById('generatedCodeSection');
                if (codeSection) {
                    codeSection.classList.remove('hidden');
                    codeSection.style.display = 'block';
                }

                showSuccess(`✅ Template loaded: ${template.name}`);

                // Scroll to code
                setTimeout(() => {
                    if (codeSection) {
                        codeSection.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }, 100);
            } else {
                showError('Failed to load template: ' + (response?.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error loading template:', error);
            showError('Error loading template: ' + error.message);
        }
    }

    /**
     * Run backtest
     */
    async runBacktest() {
        console.log('=== RUN BACKTEST CALLED ===');

        const code = document.getElementById('strategyCode').value.trim();
        const symbol = document.getElementById('btSymbol').value.trim();
        const timeframe = document.getElementById('btTimeframe').value;
        const balance = parseFloat(document.getElementById('btBalance').value);
        const startDate = document.getElementById('btStartDate').value;
        const endDate = document.getElementById('btEndDate').value;
        const lotSize = parseFloat(document.getElementById('btLotSize').value);
        const spread = parseInt(document.getElementById('btSpread').value);

        console.log('Backtest parameters:', {
            codeLength: code.length,
            symbol,
            timeframe,
            balance,
            startDate,
            endDate,
            lotSize,
            spread
        });

        // Validate inputs
        if (!code) {
            console.error('No strategy code');
            showError('No strategy code provided');
            return;
        }

        if (!symbol) {
            console.error('No symbol');
            showError('Please enter a symbol');
            return;
        }

        if (!startDate || !endDate) {
            console.error('Missing dates');
            showError('Please select date range');
            return;
        }

        if (balance <= 0) {
            console.error('Invalid balance');
            showError('Initial balance must be greater than 0');
            return;
        }

        try {
            const btn = document.getElementById('runBacktestBtn');
            btn.disabled = true;
            btn.textContent = '⏳ Running backtest...';

            showInfo('Running backtest... This may take a few seconds.');

            console.log('Sending backtest request to backend...');

            // Send to backend
            const response = await mt5Connector.sendMessage({
                action: 'run_backtest',
                strategy_code: code,
                symbol: symbol,
                timeframe: timeframe,
                initial_balance: balance,
                start_date: startDate,
                end_date: endDate,
                lot_size: lotSize,
                spread_points: spread
            });

            console.log('Backtest response received:', response);

            btn.disabled = false;
            btn.textContent = '🚀 Start Backtest';

            if (response.success) {
                console.log('Backtest successful, displaying results');
                this.displayResults(response);
                showSuccess('Backtest completed successfully!');
            } else {
                console.error('Backtest failed:', response.error);
                showError('Backtest failed: ' + (response.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Backtest error:', error);
            const btn = document.getElementById('runBacktestBtn');
            btn.disabled = false;
            btn.textContent = '🚀 Start Backtest';
            showError('Error running backtest: ' + error.message);
        }
    }

    /**
     * Display backtest results
     */
    displayResults(response) {
        const metrics = response.metrics;
        const trades = response.trades;
        const equityCurve = response.equity_curve;

        // Update metrics
        setText('btNetProfit', formatCurrency(metrics.net_profit));
        setText('btWinRate', metrics.win_rate + '%');
        setText('btProfitFactor', metrics.profit_factor.toFixed(2));
        setText('btMaxDD', metrics.max_drawdown_pct.toFixed(2) + '%');

        setText('btTotalTrades', metrics.total_trades);
        setText('btWinningTrades', metrics.winning_trades);
        setText('btLosingTrades', metrics.losing_trades);
        setText('btReturn', metrics.return_pct.toFixed(2) + '%');

        setText('btTotalProfit', formatCurrency(metrics.total_profit));
        setText('btTotalLoss', formatCurrency(metrics.total_loss));
        setText('btAvgWin', formatCurrency(metrics.avg_win));
        setText('btAvgLoss', formatCurrency(metrics.avg_loss));
        setText('btAvgProfit', formatCurrency(metrics.avg_profit || 0));

        // Color code net profit
        const netProfitEl = document.getElementById('btNetProfit');
        if (netProfitEl) {
            netProfitEl.className = `stat-value ${metrics.net_profit >= 0 ? 'stat-positive' : 'stat-negative'}`;
        }

        // Check if backend returned price history (requires server restart)
        if (!response.price_history) {
            showError('⚠️ Backend güncellenmedi! Lütfen siyah sunucu penceresini kapatıp "Start AI Trading Coach.bat" dosyasını tekrar çalıştırın.');
            console.error('Missing price_history in response. Backend is outdated.');
            return;
        }

        // Update price chart with trades
        this.updateBacktestChart(response.price_history, trades);

        // Update trade list
        this.updateTradeList(trades);

        // Show results section
        showElement('backtestResults');

        // Scroll to results
        setTimeout(() => {
            document.getElementById('backtestResults').scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }, 100);

        // AUTO-TRIGGER OPTIMIZER (after 1 second)
        console.log('[BACKTEST] Triggering optimizer...');
        setTimeout(() => {
            if (typeof showOptimizerResults === 'function') {
                showOptimizerResults(response);
            } else {
                console.error('[BACKTEST] showOptimizerResults not found!');
            }
        }, 1500);
    }

    /**
     * Update backtest chart (Price + Trades)
     */
    updateBacktestChart(priceHistory, trades) {
        this.initBacktestChart();

        if (!this.equityCurveChart || !priceHistory || priceHistory.length === 0) {
            return;
        }

        const labels = priceHistory.map(candle => {
            const date = new Date(candle.time);
            return date.toLocaleDateString('tr-TR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        });

        const data = priceHistory.map(candle => candle.close);

        // Prepare trade markers
        const buyPoints = new Array(priceHistory.length).fill(null);
        const sellPoints = new Array(priceHistory.length).fill(null);

        // Map trades to closest time points
        trades.forEach(trade => {
            const entryTime = new Date(trade.entry_time).getTime();

            // Find closest candle index
            let closestIndex = -1;
            let minDiff = Infinity;

            priceHistory.forEach((candle, index) => {
                const candleTime = new Date(candle.time).getTime();
                const diff = Math.abs(candleTime - entryTime);
                if (diff < minDiff) {
                    minDiff = diff;
                    closestIndex = index;
                }
            });

            if (closestIndex !== -1) {
                if (trade.type === 'LONG') {
                    buyPoints[closestIndex] = trade.entry_price;
                } else {
                    sellPoints[closestIndex] = trade.entry_price;
                }
            }
        });

        this.equityCurveChart.data.labels = labels;
        this.equityCurveChart.data.datasets = [
            {
                label: 'Fiyat',
                data: data,
                borderColor: 'rgba(102, 126, 234, 0.8)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 0,
                fill: false,
                order: 2
            },
            {
                label: 'Alış (Buy)',
                data: buyPoints,
                backgroundColor: '#38ef7d', // Green
                borderColor: '#38ef7d',
                pointStyle: 'triangle',
                pointRadius: 8,
                pointHoverRadius: 10,
                showLine: false,
                order: 1
            },
            {
                label: 'Satış (Sell)',
                data: sellPoints,
                backgroundColor: '#f45c43', // Red
                borderColor: '#f45c43',
                pointStyle: 'triangle',
                rotation: 180, // Point down
                pointRadius: 8,
                pointHoverRadius: 10,
                showLine: false,
                order: 1
            }
        ];

        this.equityCurveChart.update();

        // Store price history and trades for popup
        this.priceHistory = priceHistory;
        this.currentTrades = trades;
        this.tradeIndexMap = {};  // Map chart index to trade

        trades.forEach(trade => {
            const entryTime = new Date(trade.entry_time).getTime();
            let closestIndex = -1;
            let minDiff = Infinity;

            priceHistory.forEach((candle, index) => {
                const candleTime = new Date(candle.time).getTime();
                const diff = Math.abs(candleTime - entryTime);
                if (diff < minDiff) {
                    minDiff = diff;
                    closestIndex = index;
                }
            });

            if (closestIndex !== -1) {
                this.tradeIndexMap[closestIndex] = trade;
            }
        });
    }

    /**
     * Show trade detail popup with candlestick chart
     */
    showTradePopup(chartIndex, type) {
        const trade = this.tradeIndexMap[chartIndex];
        if (!trade) return;

        // Get nearby candles for the mini chart (50 candles before, 50 after = ~100 total)
        const startIdx = Math.max(0, chartIndex - 50);
        const endIdx = Math.min(this.priceHistory.length - 1, chartIndex + 50);
        const candles = this.priceHistory.slice(startIdx, endIdx + 1);
        const entryIndex = chartIndex - startIdx;  // Entry position in the slice

        // Create popup if not exists
        let popup = document.getElementById('tradeDetailPopup');
        if (!popup) {
            popup = document.createElement('div');
            popup.id = 'tradeDetailPopup';
            popup.className = 'trade-popup';
            popup.innerHTML = `
                <div class="trade-popup-content glass-card" style="max-width: 900px;">
                    <div class="trade-popup-header">
                        <span id="tradePopupType"></span>
                        <button class="btn btn-ghost btn-sm" onclick="backtest.closeTradePopup()">✕</button>
                    </div>
                    <div class="trade-chart-container">
                        <canvas id="tradeCandleChart" width="850" height="280"></canvas>
                    </div>
                    <div class="trade-legend">
                        <span class="legend-item"><span class="legend-dot entry"></span>Entry</span>
                        <span class="legend-item"><span class="legend-dot tp"></span>TP</span>
                        <span class="legend-item"><span class="legend-dot sl"></span>SL</span>
                    </div>
                    <div class="trade-details" style="margin-top: 12px;">
                        <div class="trade-row">
                            <span>📅 Giriş:</span>
                            <span id="tradeEntryTime"></span>
                        </div>
                        <div class="trade-row">
                            <span>💰 Sonuç:</span>
                            <span id="tradeProfit"></span>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(popup);

            // Add styles
            const style = document.createElement('style');
            style.textContent = `
                .trade-popup {
                    position: fixed;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    background: rgba(0,0,0,0.8);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }
                .trade-popup-content {
                    padding: var(--space-lg);
                    animation: popIn 0.2s ease;
                }
                @keyframes popIn {
                    from { transform: scale(0.9); opacity: 0; }
                    to { transform: scale(1); opacity: 1; }
                }
                .trade-popup-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--space-md);
                    font-size: 1.2rem;
                    font-weight: 600;
                }
                .trade-chart-container {
                    background: #0d1117;
                    border-radius: var(--radius-md);
                    padding: 10px;
                    margin-bottom: 10px;
                }
                .trade-legend {
                    display: flex;
                    justify-content: center;
                    gap: 20px;
                    font-size: 0.85rem;
                }
                .legend-item {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                .legend-dot {
                    width: 12px;
                    height: 3px;
                    border-radius: 2px;
                }
                .legend-dot.entry { background: #667eea; }
                .legend-dot.tp { background: #38ef7d; }
                .legend-dot.sl { background: #f45c43; }
                .trade-row {
                    display: flex;
                    justify-content: space-between;
                    padding: var(--space-sm) 0;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                }
                .trade-row:last-child { border-bottom: none; }
            `;
            document.head.appendChild(style);
        }

        // Fill popup data
        const isLong = trade.type === 'LONG';
        const isProfit = trade.profit >= 0;

        document.getElementById('tradePopupType').innerHTML = isLong
            ? '<span style="color: #38ef7d;">📈 LONG</span>'
            : '<span style="color: #f45c43;">📉 SHORT</span>';

        document.getElementById('tradeEntryTime').textContent = new Date(trade.entry_time).toLocaleString('tr-TR');
        document.getElementById('tradeProfit').innerHTML = `<span style="color: ${isProfit ? '#38ef7d' : '#f45c43'}; font-weight: bold;">${isProfit ? '+' : ''}$${trade.profit.toFixed(2)}</span>`;

        // Draw candlestick chart
        this.drawCandlestickChart(candles, entryIndex, trade);

        // Show popup
        popup.style.display = 'flex';
    }

    /**
     * Draw candlestick chart on canvas
     */
    drawCandlestickChart(candles, entryIndex, trade) {
        const canvas = document.getElementById('tradeCandleChart');
        if (!canvas || candles.length === 0) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.fillStyle = '#0d1117';
        ctx.fillRect(0, 0, width, height);

        // Calculate price range
        const prices = candles.flatMap(c => [c.high, c.low]);
        const entryPrice = trade.entry_price;
        const exitPrice = trade.exit_price;

        // Include SL/TP in range
        const isLong = trade.type === 'LONG';
        const risk = Math.abs(entryPrice - exitPrice);
        const slPrice = isLong ? entryPrice - risk : entryPrice + risk;
        const tpPrice = exitPrice;

        prices.push(entryPrice, exitPrice, slPrice);

        const minPrice = Math.min(...prices) * 0.9999;
        const maxPrice = Math.max(...prices) * 1.0001;
        const priceRange = maxPrice - minPrice;

        const padding = 40;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding;

        const candleWidth = Math.floor(chartWidth / candles.length) - 2;
        const candleSpacing = chartWidth / candles.length;

        // Helper to convert price to Y
        const priceToY = (price) => padding + (1 - (price - minPrice) / priceRange) * chartHeight;

        // Draw grid lines
        ctx.strokeStyle = 'rgba(255,255,255,0.1)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = padding + (chartHeight / 4) * i;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - 10, y);
            ctx.stroke();

            // Price label
            const price = maxPrice - (priceRange / 4) * i;
            ctx.fillStyle = '#6b7280';
            ctx.font = '10px Arial';
            ctx.fillText(price.toFixed(5), 2, y + 3);
        }

        // Draw candles
        candles.forEach((candle, i) => {
            const x = padding + i * candleSpacing + candleSpacing / 2;
            const isUp = candle.close >= candle.open;

            // Highlight entry candle
            const isEntry = i === entryIndex;

            // Candle body
            const bodyTop = priceToY(Math.max(candle.open, candle.close));
            const bodyBottom = priceToY(Math.min(candle.open, candle.close));
            const bodyHeight = Math.max(1, bodyBottom - bodyTop);

            // Wick
            ctx.strokeStyle = isUp ? '#38ef7d' : '#f45c43';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(x, priceToY(candle.high));
            ctx.lineTo(x, priceToY(candle.low));
            ctx.stroke();

            // Body
            ctx.fillStyle = isUp ? '#38ef7d' : '#f45c43';
            if (isEntry) {
                ctx.fillStyle = '#667eea';  // Highlight entry
            }
            ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);

            // Entry marker
            if (isEntry) {
                ctx.fillStyle = '#667eea';
                ctx.beginPath();
                ctx.moveTo(x, bodyBottom + 5);
                ctx.lineTo(x - 5, bodyBottom + 12);
                ctx.lineTo(x + 5, bodyBottom + 12);
                ctx.fill();
            }
        });

        // Draw Entry line (blue dashed)
        ctx.strokeStyle = '#667eea';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 3]);
        ctx.beginPath();
        ctx.moveTo(padding, priceToY(entryPrice));
        ctx.lineTo(width - 10, priceToY(entryPrice));
        ctx.stroke();
        ctx.fillStyle = '#667eea';
        ctx.font = 'bold 11px Arial';
        ctx.fillText('Entry ' + entryPrice.toFixed(5), width - 100, priceToY(entryPrice) - 5);

        // Draw TP line (green)
        if (trade.profit >= 0) {
            ctx.strokeStyle = '#38ef7d';
        } else {
            ctx.strokeStyle = '#f45c43';
        }
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 3]);
        ctx.beginPath();
        ctx.moveTo(padding, priceToY(exitPrice));
        ctx.lineTo(width - 10, priceToY(exitPrice));
        ctx.stroke();
        ctx.fillStyle = trade.profit >= 0 ? '#38ef7d' : '#f45c43';
        ctx.fillText((trade.profit >= 0 ? 'TP ' : 'SL ') + exitPrice.toFixed(5), width - 100, priceToY(exitPrice) - 5);

        ctx.setLineDash([]);  // Reset
    }

    /**
     * Close trade popup
     */
    closeTradePopup() {
        const popup = document.getElementById('tradeDetailPopup');
        if (popup) {
            popup.style.display = 'none';
        }
    }

    /**
     * Update trade list
     */
    updateTradeList(trades) {
        const container = document.getElementById('tradesList');
        if (!container) return;

        if (!trades || trades.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No trades executed</div>';
            return;
        }

        // Performance Fix: Store trades and render first batch
        this.currentTrades = trades;
        this.visibleTrades = Math.min(trades.length, this.batchSize);

        this.renderTradesBatch(container);
    }

    /**
     * Render a batch of trades
     */
    renderTradesBatch(container) {
        const tradesToRender = this.currentTrades.slice(0, this.visibleTrades);

        let html = tradesToRender.map((trade, index) => {
            const isProfit = trade.profit >= 0;
            const entryDate = new Date(trade.entry_time).toLocaleString('tr-TR');
            const exitDate = new Date(trade.exit_time).toLocaleString('tr-TR');

            return `
                <div class="glass-card mb-sm" style="padding: var(--space-sm);">
                    <div class="flex justify-between items-center">
                        <div>
                            <div style="font-weight: 600;">#${index + 1} - ${trade.type}</div>
                            <div class="text-sm text-secondary">
                                Entry: ${entryDate} @ ${trade.entry_price.toFixed(5)}
                            </div>
                            <div class="text-sm text-secondary">
                                Exit: ${exitDate} @ ${trade.exit_price.toFixed(5)}
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="${isProfit ? 'stat-positive' : 'stat-negative'}" style="font-weight: 600; font-size: 1.1rem;">
                                ${formatCurrency(trade.profit)}
                            </div>
                            <div class="text-sm text-secondary">
                                Balance: ${formatCurrency(trade.balance)}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Add "Show More" if there are more trades
        if (this.visibleTrades < this.currentTrades.length) {
            html += `
                <div class="text-center mt-md mb-md">
                    <button class="btn btn-outline btn-sm" onclick="backtest.showMoreTrades()">
                        ➕ Daha Fazla Göster (${this.currentTrades.length - this.visibleTrades} kaldı)
                    </button>
                </div>
            `;
        }

        container.innerHTML = html;
    }

    /**
     * Show next batch of trades
     */
    showMoreTrades() {
        const container = document.getElementById('tradesList');
        if (!container) return;

        this.visibleTrades = Math.min(this.currentTrades.length, this.visibleTrades + this.batchSize);
        this.renderTradesBatch(container);

        // Scroll a bit to show newly loaded items
        const lastCard = container.querySelector('.glass-card:last-of-type');
        if (lastCard) {
            lastCard.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }
}

// Create global instance
const backtest = new Backtest();

// Global functions for HTML onclick handlers
window.generateStrategy = () => backtest.generateStrategy();
window.showBacktestParams = () => backtest.showBacktestParams();
window.clearStrategy = () => backtest.clearStrategy();
window.loadTemplate = () => backtest.loadTemplate();
window.runBacktest = () => backtest.runBacktest();

// Go Live with current strategy
window.goLiveWithStrategy = async () => {
    const strategyCode = document.getElementById('strategyCode')?.value;

    if (!strategyCode || !strategyCode.trim()) {
        showError('Önce bir strateji oluşturun veya şablon seçin');
        return;
    }

    // Create live trading modal
    let modal = document.getElementById('liveTradeModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'liveTradeModal';
        modal.className = 'trade-popup';
        modal.innerHTML = `
            <div class="trade-popup-content glass-card" style="max-width: 550px;">
                <div class="trade-popup-header">
                    <span>🚀 Canlı İşleme Al</span>
                    <button class="btn btn-ghost btn-sm" onclick="closeLiveModal()">✕</button>
                </div>
                <div style="padding: 1rem 0;">
                    <div class="form-group">
                        <label class="form-label">📋 Strateji/Şablon Seç</label>
                        <select id="liveTemplateSelect" class="form-select" onchange="loadTemplateForLive()">
                            <option value="">-- Mevcut kodu kullan --</option>
                        </select>
                        <small class="text-secondary">Kayıtlı şablonlardan birini seçin veya mevcut kodu kullanın</small>
                    </div>
                    <div class="form-group">
                        <label class="form-label">💹 Sembol</label>
                        <select id="liveSymbol" class="form-select">
                            <option value="EURUSD">EURUSD</option>
                            <option value="GBPUSD">GBPUSD</option>
                            <option value="USDJPY">USDJPY</option>
                            <option value="XAUUSD">XAUUSD (Gold)</option>
                            <option value="BTCUSD">BTCUSD</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">⏱️ Zaman Dilimi</label>
                        <select id="liveTimeframe" class="form-select">
                            <option value="M5">M5</option>
                            <option value="M15">M15</option>
                            <option value="H1" selected>H1</option>
                            <option value="H4">H4</option>
                        </select>
                    </div>
                    <div class="grid grid-2 gap-md">
                        <div class="form-group">
                            <label class="form-label">📊 Lot Büyüklüğü</label>
                            <input type="number" id="liveLotSize" class="form-input" value="0.01" step="0.01">
                        </div>
                        <div class="form-group">
                            <label class="form-label">🎯 Risk:Reward</label>
                            <input type="number" id="liveRR" class="form-input" value="2" step="0.5">
                        </div>
                    </div>
                    <div class="flex gap-md mt-lg">
                        <button class="btn btn-success" onclick="startLiveTrading()" style="flex: 1; background: linear-gradient(135deg, #10b981, #059669);">
                            ▶️ Canlı Başlat
                        </button>
                        <button class="btn btn-outline" onclick="closeLiveModal()">İptal</button>
                    </div>
                    <p class="text-xs text-secondary mt-md" style="text-align: center;">
                        ⚠️ Önce DEMO hesapta test edin!
                    </p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // Load MT5 symbols and user templates
    await loadMT5Symbols();
    await loadTemplatesForLiveModal();

    modal.style.display = 'flex';
};

// Load MT5 symbols into dropdown
window.loadMT5Symbols = async () => {
    try {
        const response = await mt5Connector.sendMessage({ action: 'get_mt5_symbols' });
        if (response && response.data && response.data.length > 0) {
            const select = document.getElementById('liveSymbol');
            if (select) {
                select.innerHTML = response.data.map(sym =>
                    `<option value="${sym}">${sym}</option>`
                ).join('');
            }
        }
    } catch (e) {
        console.log('Could not fetch MT5 symbols, using defaults');
    }
};

// Load templates for live modal dropdown
window.loadTemplatesForLiveModal = async () => {
    const select = document.getElementById('liveTemplateSelect');
    if (!select) return;

    let options = '<option value="">-- Mevcut kodu kullan --</option>';

    // User templates
    try {
        const response = await mt5Connector.sendMessage({ action: 'get_user_templates' });
        if (response && response.data && response.data.length > 0) {
            options += '<optgroup label="👤 Benim Şablonlarım">';
            options += response.data.map(t =>
                `<option value="user:${t.id}">${t.name}</option>`
            ).join('');
            options += '</optgroup>';
        }
    } catch (e) { }

    // Built-in templates
    const builtIn = ['rsi_oversold', 'sma_crossover', 'ict_fvg', 'breakout', 'mean_reversion', 'ict_smart_money'];
    options += '<optgroup label="📦 Hazır Şablonlar">';
    options += builtIn.map(id => `<option value="builtin:${id}">${id}</option>`).join('');
    options += '</optgroup>';

    select.innerHTML = options;
};

// Load template code into strategy area
window.loadTemplateForLive = async () => {
    const select = document.getElementById('liveTemplateSelect');
    const value = select?.value;

    if (!value) return;

    if (value.startsWith('user:')) {
        const templateId = value.replace('user:', '');
        const response = await mt5Connector.sendMessage({ action: 'get_user_templates' });
        if (response?.data) {
            const template = response.data.find(t => t.id === templateId);
            if (template) {
                document.getElementById('strategyCode').value = template.code;
                showSuccess(`"${template.name}" yüklendi`);
            }
        }
    } else if (value.startsWith('builtin:')) {
        const templateId = value.replace('builtin:', '');
        document.getElementById('templateSelector').value = templateId;
        if (typeof loadTemplate === 'function') {
            await loadTemplate();
        }
    }
};

window.closeLiveModal = () => {
    const modal = document.getElementById('liveTradeModal');
    if (modal) modal.style.display = 'none';
};

window.startLiveTrading = async () => {
    const strategyCode = document.getElementById('strategyCode')?.value;
    const symbol = document.getElementById('liveSymbol')?.value || 'EURUSD';
    const timeframe = document.getElementById('liveTimeframe')?.value || 'H1';
    const lotSize = parseFloat(document.getElementById('liveLotSize')?.value) || 0.01;
    const rrRatio = parseFloat(document.getElementById('liveRR')?.value) || 2.0;

    try {
        showSuccess('Canlı işlem başlatılıyor...');

        const response = await mt5Connector.sendMessage({
            action: 'start_live_trading',
            strategy_code: strategyCode,
            symbol: symbol,
            timeframe: timeframe,
            lot_size: lotSize,
            rr_ratio: rrRatio
        });

        if (response && response.success) {
            showSuccess('✅ Canlı işlem başlatıldı! Dashboard\'dan takip edebilirsiniz.');
            closeLiveModal();
        } else {
            showError('Canlı işlem başlatılamadı: ' + (response?.error || 'Bilinmeyen hata'));
        }
    } catch (error) {
        showError('Hata: ' + error.message);
    }
};

// Save strategy as template
window.saveAsTemplate = async () => {
    const strategyCode = document.getElementById('strategyCode')?.value;
    const strategySummary = document.getElementById('strategySummaryText')?.innerText || '';

    if (!strategyCode || !strategyCode.trim()) {
        showError('Önce bir strateji oluşturun');
        return;
    }

    // Create save template modal
    let modal = document.getElementById('saveTemplateModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'saveTemplateModal';
        modal.className = 'trade-popup';
        modal.innerHTML = `
            <div class="trade-popup-content glass-card" style="max-width: 450px;">
                <div class="trade-popup-header">
                    <span>📁 Şablon Olarak Kaydet</span>
                    <button class="btn btn-ghost btn-sm" onclick="closeSaveTemplateModal()">✕</button>
                </div>
                <div style="padding: 1rem 0;">
                    <div class="form-group">
                        <label class="form-label">Şablon Adı</label>
                        <input type="text" id="templateName" class="form-input" 
                               placeholder="Örn: Benim ICT Stratejim">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Açıklama (Opsiyonel)</label>
                        <textarea id="templateDescription" class="form-input" rows="2"
                                  placeholder="Strateji hakkında kısa açıklama..."></textarea>
                    </div>
                    <div class="flex gap-md mt-lg">
                        <button class="btn btn-primary" onclick="confirmSaveTemplate()" style="flex: 1;">
                            💾 Kaydet
                        </button>
                        <button class="btn btn-outline" onclick="closeSaveTemplateModal()">İptal</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // Pre-fill description if available
    document.getElementById('templateDescription').value = strategySummary;
    modal.style.display = 'flex';
};

window.closeSaveTemplateModal = () => {
    const modal = document.getElementById('saveTemplateModal');
    if (modal) modal.style.display = 'none';
};

window.confirmSaveTemplate = async () => {
    const name = document.getElementById('templateName')?.value?.trim();
    const description = document.getElementById('templateDescription')?.value?.trim();
    const code = document.getElementById('strategyCode')?.value;

    if (!name) {
        showError('Lütfen şablon adı girin');
        return;
    }

    try {
        const response = await mt5Connector.sendMessage({
            action: 'save_user_template',
            name: name,
            description: description || '',
            code: code,
            timeframe: 'H1'
        });

        if (response && response.success) {
            showSuccess(`✅ "${name}" şablonu kaydedildi!`);
            closeSaveTemplateModal();
        } else {
            showError('Kayıt başarısız: ' + (response?.error || 'Bilinmeyen hata'));
        }
    } catch (error) {
        showError('Hata: ' + error.message);
    }
};
