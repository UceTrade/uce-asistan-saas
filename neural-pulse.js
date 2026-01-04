/**
 * Neural Pulse Intelligence (NPI) - Controller
 * Manages the high-end SMC visualization dashboard with auto-refresh and MTF analysis.
 */

class NeuralPulseController {
    constructor() {
        this.feedTasks = [
            "Price Action kütüphanesi yüklendi.",
            "Bias sistemi aktif."
        ];
        this.currentTaskIdx = 0;
        this.isRunning = false;

        // Auto-refresh feature
        this.autoRefreshInterval = null;
        this.autoRefreshSeconds = 0; // 0 = disabled
        this.lastAnalysisSymbol = 'EURUSD';

        // MTF Analysis data
        this.mtfData = {};
    }

    init() {
        console.log("[NPI] Neural Pulse Intelligence initialized.");
        this.isRunning = false;
        this.setupAutoRefreshControls();
    }

    /**
     * Setup auto-refresh controls event listeners
     */
    setupAutoRefreshControls() {
        const selector = document.getElementById('autoRefreshSelect');
        if (selector) {
            selector.addEventListener('change', (e) => {
                this.setAutoRefresh(parseInt(e.target.value));
            });
        }
    }

    /**
     * Set auto-refresh interval
     */
    setAutoRefresh(seconds) {
        // Clear existing interval
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }

        this.autoRefreshSeconds = seconds;

        if (seconds > 0) {
            this.addFeedItem(`🔄 Auto-refresh aktif: Her ${seconds} saniyede bir güncelleme`);
            this.autoRefreshInterval = setInterval(() => {
                this.triggerQuickAnalysis();
            }, seconds * 1000);
        } else {
            this.addFeedItem(`⏹️ Auto-refresh kapatıldı`);
        }

        this.updateAutoRefreshUI();
    }

    /**
     * Update auto-refresh UI indicator
     */
    updateAutoRefreshUI() {
        const indicator = document.getElementById('autoRefreshIndicator');
        if (indicator) {
            if (this.autoRefreshSeconds > 0) {
                indicator.style.display = 'inline-flex';
                indicator.innerHTML = `<span class="pulse-dot"></span> ${this.autoRefreshSeconds}s`;
            } else {
                indicator.style.display = 'none';
            }
        }
    }

    /**
     * Trigger MTF (Multi-Timeframe) Analysis
     */
    async triggerMTFAnalysis() {
        const symbol = document.getElementById('neuralSymbol').value;
        this.addFeedItem(`📊 ${symbol} MTF analizi başlatılıyor...`);

        try {
            if (!window.mt5Connector || !window.mt5Connector.connected) {
                this.addFeedItem("❌ Hata: MT5 bağlantı modülü bulunamadı.");
                return;
            }

            const response = await window.mt5Connector.sendMessage({
                action: 'mtf_analysis',
                symbol: symbol,
                preset: 'intraday'
            });

            if (response && !response.error) {
                this.mtfData = response;
                this.updateMTFDisplay(response);
                this.addFeedItem(`✅ ${symbol} MTF analizi tamamlandı`);
            } else {
                this.addFeedItem(`❌ MTF Hata: ${response?.error || 'Bilinmeyen hata'}`);
            }
        } catch (error) {
            console.error("[NPI] MTF Analysis failed:", error);
            this.addFeedItem(`❌ MTF hatası: ${error.message}`);
        }
    }

    /**
     * Update MTF display panel
     */
    updateMTFDisplay(data) {
        const container = document.getElementById('mtfAnalysisContainer');
        if (!container) return;

        const timeframes = data.timeframes || [];
        const confluence = data.confluence || {};

        let html = `
            <div class="mtf-grid">
                ${timeframes.map(tf => `
                    <div class="mtf-item ${tf.bias > 0 ? 'bullish' : tf.bias < 0 ? 'bearish' : 'neutral'}">
                        <div class="mtf-tf">${tf.timeframe}</div>
                        <div class="mtf-bias">${tf.bias > 0 ? '🟢 BULLISH' : tf.bias < 0 ? '🔴 BEARISH' : '⚪ NEUTRAL'}</div>
                        <div class="mtf-score">${(tf.score * 100).toFixed(0)}%</div>
                    </div>
                `).join('')}
            </div>
            <div class="mtf-confluence mt-sm">
                <span class="text-secondary">Confluence:</span>
                <span class="${confluence.direction === 'BULLISH' ? 'text-success' : confluence.direction === 'BEARISH' ? 'text-danger' : 'text-muted'}">
                    ${confluence.direction || 'N/A'} (${confluence.strength || 0}%)
                </span>
            </div>
        `;

        container.innerHTML = html;
        container.style.display = 'block';
    }


    startFeed() {
        // Automation disabled as per user request.
        // Feed items are now added only when real data is processed or analysis is triggered.
    }

    addFeedItem(text) {
        const feedContainer = document.getElementById('intelligenceFeed');
        if (!feedContainer) return;

        const now = new Date();
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

        // Use requestAnimationFrame for smoother DOM updates (NEW: Performance fix)
        requestAnimationFrame(() => {
            const item = document.createElement('div');
            item.className = 'feed-item';
            item.innerHTML = `
                <span class="feed-time">${timeStr}</span>
                <span class="feed-text">${text}</span>
            `;

            feedContainer.prepend(item);

            if (feedContainer.children.length > 10) {
                feedContainer.removeChild(feedContainer.lastChild);
            }
        });
    }

    animateGauges() {
        // No initial animation
    }

    updateBias(value, label) {
        const gauge = document.getElementById('biasGauge');
        const valueBox = document.getElementById('biasValue');
        const reasoning = document.getElementById('biasReasoning');

        if (!gauge) return;

        // Map 0-100 to 0-180 degrees
        const rotation = (value / 100) * 180;
        gauge.style.transform = `rotate(${rotation}deg)`;
        valueBox.innerText = label;

        if (label === "BEARISH") {
            valueBox.style.color = "#f45c43";
        } else if (label === "BULLISH") {
            valueBox.style.color = "#38ef7d";
        } else {
            valueBox.style.color = "white";
        }
    }

    updateWithRealData(marketData) {
        const smc = marketData.smc;
        if (!smc) return;

        console.log("[NPI] Updating with real SMC data:", smc);

        // 1. Update Gauge based on trend_bias
        let biasLabel = "NEUTRAL";
        let biasValue = 50;

        if (smc.trend_bias === 1) {
            biasLabel = "BULLISH";
            biasValue = 85;
        } else if (smc.trend_bias === -1) {
            biasLabel = "BEARISH";
            biasValue = 15;
        }
        this.updateBias(biasValue, biasLabel);

        // 2. Update Structure List
        const structureList = document.getElementById('structureList');
        if (structureList) {
            structureList.innerHTML = `
                <div class="structure-item">
                    <span>Market Trend (BOS)</span>
                    <span class="badge ${smc.bos_detected ? 'badge-success' : 'badge-outline'}">${smc.bos_detected ? 'CONTINUATION' : 'NORMAL'}</span>
                </div>
                <div class="structure-item">
                    <span>Reversal Sign (CHoCH)</span>
                    <span class="badge ${smc.choch_detected ? 'badge-warning' : 'badge-outline'}">${smc.choch_detected ? 'REVERSAL' : 'NO CHANGE'}</span>
                </div>
                <div class="structure-item">
                    <span>Structural Power</span>
                    <span class="badge badge-info">${smc.bos_count} Structures Found</span>
                </div>
            `;
        }

        // 3. Update Liquidity Pulse
        const liquidList = document.getElementById('liquidList');
        // If we don't have liquidList ID in HTML, let's target the card children
        // Assuming we need to update EQH/EQL prices
        const eqhLabel = document.getElementById('eqhLine');
        const eqlLabel = document.getElementById('eqlLine');
        if (eqhLabel) eqhLabel.innerText = smc.eqh_price > 0 ? `EQH Range: ${smc.eqh_price.toFixed(5)}` : "EQH: Not Detected";
        if (eqlLabel) eqlLabel.innerText = smc.eql_price > 0 ? `EQL Range: ${smc.eql_price.toFixed(5)}` : "EQL: Not Detected";

        const liquidText = document.querySelector('.liquid-card p') || document.querySelector('.liquid-desc');
        if (liquidText) {
            if (smc.sweep_high || smc.sweep_low) {
                liquidText.innerText = "🚨 LİKİDİTE SÜPÜRMESİ: Piyasa büyük emirleri topladı!";
                liquidText.style.color = "#ffcc00";
            } else {
                liquidText.innerText = "Likidite havuzları stabil, beklenen bir sweep yok.";
                liquidText.style.color = "rgba(255,255,255,0.6)";
            }
        }

        // 4. Update Intelligence Feed
        if (smc.choch_detected) {
            this.addFeedItem(`⚠️ KRİTİK: ${marketData.symbol} üzerinde Trend Dönüşü (CHoCH) saptandı!`);
        }
        if (smc.sweep_high || smc.sweep_low) {
            this.addFeedItem(`🎯 LİKİDİTE SÜPÜRMESİ: ${marketData.symbol} likidite topladı.`);
        }
        if (smc.bullish_ob || smc.bearish_ob) {
            this.addFeedItem(`🏦 KURUMSAL EMİR: ${smc.bullish_ob ? 'Bullish' : 'Bearish'} Order Block oluştu.`);
        }

        if (marketData.off_market) {
            this.addFeedItem(`📅 HAFTASONU MODU: Piyasalar kapalı. Son kapanış verileri kullanılıyor.`);
        }

        this.addFeedItem(`🔍 ${marketData.symbol} tarandı. Bias: ${biasLabel}`);

        // 5. Update Session Badge
        const sessionBadge = document.getElementById('sessionBadge');
        const sessionName = document.getElementById('sessionName');
        const sessionDot = document.querySelector('.session-dot');
        if (sessionBadge && smc.session_info) {
            sessionBadge.style.display = 'flex';
            sessionName.innerText = smc.session_info.name;
            if (sessionDot) {
                sessionDot.style.background = smc.session_info.color;
                sessionDot.style.boxShadow = `0 0 10px ${smc.session_info.color}`;
            }
        }

        // 6. Update Coach Advice
        const coachAdvice = document.getElementById('coachAdvice');
        const coachText = document.getElementById('coachText');
        if (coachAdvice && smc.coach_advice) {
            coachAdvice.style.display = 'flex';
            coachText.innerText = smc.coach_advice;
        }

        // 7. Update Reasoning
        const reasoning = document.getElementById('biasReasoning');
        if (reasoning) {
            let statusPrefix = marketData.off_market ? "[OFFLINE] " : "";
            reasoning.innerText = `${statusPrefix}Piyasada ${smc.bos_count} adet yapı kırılımı saptandı. ${smc.is_discount ? 'İndirim (Discount)' : smc.is_premium ? 'Premium' : 'Denge'} bölgesindeyiz.`;
            if (marketData.off_market) reasoning.style.color = "#ffcc00";
            else reasoning.style.color = "white";
        }
    }

    async triggerQuickAnalysis() {
        const symbol = document.getElementById('neuralSymbol').value;
        this.addFeedItem(`🚀 ${symbol} için derin zeka taraması başlatıldı...`);

        try {
            if (!window.mt5Connector) {
                this.addFeedItem("❌ Hata: MT5 bağlantı modülü bulunamadı.");
                return;
            }

            if (!window.mt5Connector.connected) {
                this.addFeedItem("❌ Hata: Sunucuya bağlı değil. Lütfen terminalden sunucuyu çalıştırın.");
                return;
            }

            const response = await window.mt5Connector.sendMessage({
                action: 'get_market_analysis',
                symbol: symbol
            });

            // The mt5Connector unwraps the 'data' property before returning
            if (response) {
                if (response.error) {
                    this.addFeedItem(`❌ Hata: ${response.error}`);
                } else {
                    this.updateWithRealData(response);
                    this.drawOracle(response.forecast); // Draw future projection
                    this.addFeedItem(`✅ ${symbol} analizi başarıyla sonuçlandı.`);
                }
            }
        } catch (error) {
            console.error("[NPI] Trigger failed:", error);
            this.addFeedItem(`❌ Tarama hatası: ${error.message}`);
        }
    }

    async triggerRadar() {
        this.addFeedItem("🛰️ RADAR: Tüm piyasa taranıyor...");
        const grid = document.getElementById('radarGrid');
        if (grid) grid.innerHTML = '<div class="radar-placeholder">Tarama devam ediyor... 🛰️</div>';

        try {
            const response = await window.mt5Connector.sendMessage({
                action: 'run_global_scan',
                symbols: ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD', 'AUDUSD', 'EURJPY', 'ETHUSD', 'GBPCHF', 'USDCAD', 'NZDUSD', 'EURGBP', 'EURCAD', 'AUDJPY', 'GBPJPY', 'CHFHUF', 'XAGUSD', 'USOUSD', 'SPX500', 'NAS100'],
                requestTimeout: 120000 // 120 seconds for deep global scan
            });

            if (response && response.results) {
                if (response.results.length === 0) {
                    this.addFeedItem("⚠️ RADAR: Hiçbir sembol analiz edilemedi. Lütfen paritelerin MT5 'Piyasa Gözlemi' (Market Watch) listesinde açık olduğundan emin olun.");
                    grid.innerHTML = '<div class="radar-placeholder">Sembol bulunamadı. Lütfen MT5 Market Watch listesini güncelleyip tekrar deneyin.</div>';
                } else {
                    this.updateRadarGrid(response.results);
                    this.addFeedItem(`🛰️ RADAR: ${response.results.length} sembol analiz edildi.`);
                }
            } else {
                this.addFeedItem("❌ Radar: Beklenmedik bir yanıt formatı alındı.");
            }
        } catch (e) {
            console.error("[NPI] Radar failed:", e);
            if (e.message.includes("zaman aşımı")) {
                this.addFeedItem("⏳ Radar: İstek zaman aşımına uğradı. Market kapalı olabilir veya bağlantı yavaş.");
            } else {
                this.addFeedItem("❌ Radar taraması başarısız oldu. Sunucu bağlantısını kontrol edin.");
            }
        }
    }

    updateRadarGrid(results) {
        const grid = document.getElementById('radarGrid');
        if (!grid) return;

        // Store results for filtering
        this.radarResults = results;

        // Get current view mode and filter
        const viewMode = document.getElementById('radarViewMode')?.value || 'grid';
        const categoryFilter = document.getElementById('radarCategoryFilter')?.value || 'all';

        // Apply category filter
        let filteredResults = this.filterByCategory(results, categoryFilter);

        // Sort by score descending
        filteredResults.sort((a, b) => b.score - a.score);

        grid.innerHTML = '';

        if (viewMode === 'heatmap') {
            this.renderHeatmapView(grid, filteredResults);
        } else {
            this.renderGridView(grid, filteredResults);
        }
    }

    /**
     * Filter results by category
     */
    filterByCategory(results, category) {
        if (category === 'all') return results;

        const categories = {
            'major': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD'],
            'minor': ['EURGBP', 'EURJPY', 'EURCAD', 'EURAUD', 'GBPJPY', 'GBPCHF', 'AUDJPY', 'CADJPY'],
            'crypto': ['BTCUSD', 'ETHUSD', 'XRPUSD', 'LTCUSD'],
            'metals': ['XAUUSD', 'XAGUSD'],
            'indices': ['SPX500', 'NAS100', 'US30', 'GER40'],
            'commodities': ['USOUSD', 'UKOUSD']
        };

        const categorySymbols = categories[category] || [];
        return results.filter(r => categorySymbols.includes(r.symbol));
    }

    /**
     * Render grid view (default)
     */
    renderGridView(grid, results) {
        results.forEach(res => {
            const item = document.createElement('div');
            const isHigh = res.score >= 70;
            const isMedium = res.score >= 50 && res.score < 70;

            item.className = `radar-item ${isHigh ? 'high-confluence' : isMedium ? 'medium-confluence' : ''}`;
            item.dataset.symbol = res.symbol;

            item.innerHTML = `
                <div class="radar-name">${res.symbol}</div>
                <div class="radar-score">${res.score.toFixed(0)}%</div>
                <div class="radar-bias" style="color: ${res.bias === 'BULLISH' || res.bias === 'uptrend' ? '#38ef7d' : res.bias === 'BEARISH' || res.bias === 'downtrend' ? '#ff0080' : '#a0aec0'}">${this.formatBias(res.bias)}</div>
            `;

            // Click to analyze
            item.addEventListener('click', () => {
                document.getElementById('neuralSymbol').value = res.symbol;
                this.triggerQuickAnalysis();
            });

            grid.appendChild(item);
        });
    }

    /**
     * Render heatmap view
     */
    renderHeatmapView(grid, results) {
        grid.classList.add('heatmap-mode');

        // Find max score for normalization
        const maxScore = Math.max(...results.map(r => r.score), 1);

        results.forEach(res => {
            const item = document.createElement('div');
            const normalizedScore = res.score / 100;

            // Color based on bias and score
            let bgColor;
            if (res.bias === 'BULLISH' || res.bias === 'uptrend') {
                bgColor = `rgba(56, 239, 125, ${normalizedScore * 0.8})`;
            } else if (res.bias === 'BEARISH' || res.bias === 'downtrend') {
                bgColor = `rgba(255, 0, 128, ${normalizedScore * 0.8})`;
            } else {
                bgColor = `rgba(160, 174, 192, ${normalizedScore * 0.5})`;
            }

            item.className = 'heatmap-cell';
            item.style.background = bgColor;
            item.dataset.symbol = res.symbol;

            item.innerHTML = `
                <div class="heatmap-symbol">${res.symbol}</div>
                <div class="heatmap-score">${res.score.toFixed(0)}%</div>
            `;

            // Click to analyze
            item.addEventListener('click', () => {
                document.getElementById('neuralSymbol').value = res.symbol;
                this.triggerQuickAnalysis();
            });

            grid.appendChild(item);
        });
    }

    /**
     * Format bias text
     */
    formatBias(bias) {
        if (bias === 'uptrend' || bias === 'BULLISH') return '🟢 LONG';
        if (bias === 'downtrend' || bias === 'BEARISH') return '🔴 SHORT';
        return '⚪ FLAT';
    }

    /**
     * Set radar auto-scan interval
     */
    setRadarAutoScan(seconds) {
        if (this.radarAutoScanInterval) {
            clearInterval(this.radarAutoScanInterval);
            this.radarAutoScanInterval = null;
        }

        if (seconds > 0) {
            this.addFeedItem(`🛰️ Radar auto-scan: Her ${seconds / 60} dakikada bir tarama`);
            this.radarAutoScanInterval = setInterval(() => {
                this.triggerRadar();
            }, seconds * 1000);
        } else {
            this.addFeedItem(`⏹️ Radar auto-scan kapatıldı`);
        }
    }

    /**
     * Apply radar filter (called from UI)
     */
    applyRadarFilter() {
        if (this.radarResults) {
            this.updateRadarGrid(this.radarResults);
        }
    }


    drawOracle(forecast) {
        const canvas = document.getElementById('oracleCanvas');
        if (!canvas || !forecast) return;

        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();

        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);

        const w = rect.width;
        const h = rect.height;

        ctx.clearRect(0, 0, w, h);

        // Grid lines for high tech feel
        ctx.strokeStyle = 'rgba(255,255,255,0.05)';
        ctx.lineWidth = 1;
        for (let i = 0; i < w; i += 40) {
            ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, h); ctx.stroke();
        }
        for (let i = 0; i < h; i += 40) {
            ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(w, i); ctx.stroke();
        }

        // Draw paths
        this._drawPath(ctx, forecast.primary, '#38ef7d', w, h);
        this._drawPath(ctx, forecast.secondary, '#ff0080', w, h);
    }

    _drawPath(ctx, points, color, w, h) {
        if (!points || points.length === 0) return;

        // Scaling logic based on path coordinates
        const yVals = points.map(p => p.y);
        const minVal = Math.min(...yVals) * 0.9995;
        const maxVal = Math.max(...yVals) * 1.0005;
        const yRange = maxVal - minVal;

        const maxX = Math.max(...points.map(p => p.x));

        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.shadowBlur = 15;
        ctx.shadowColor = color;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';

        points.forEach((p, i) => {
            const x = (p.x / maxX) * (w * 0.8); // Use 80% of width
            const y = h - ((p.y - minVal) / yRange) * h;

            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });

        ctx.stroke();
        ctx.shadowBlur = 0;

        // Add glow dot at the end
        const last = points[points.length - 1];
        const lx = (last.x / maxX) * (w * 0.8);
        const ly = h - ((last.y - minVal) / yRange) * h;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(lx, ly, 4, 0, Math.PI * 2);
        ctx.fill();
    }

    updateSimulatedMetrics() {
        // Obsolete per user request
    }
}

// Global instance
window.neuralPulse = new NeuralPulseController();
