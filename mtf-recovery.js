/**
 * Multi-Timeframe Analysis & Recovery Planner - Frontend Controller
 * Provides MTF analysis UI and drawdown recovery visualization
 */

// ============================================
// MULTI-TIMEFRAME ANALYSIS
// ============================================

class MTFAnalyzer {
    constructor() {
        this.currentData = null;
    }

    async analyze(symbol, preset = 'intraday') {
        try {
            const response = await mt5Connector.sendMessage({
                action: 'mtf_analysis',
                symbol: symbol,
                preset: preset
            });

            if (response && response.data) {
                this.currentData = response.data;
                this.render();
                return true;
            }
            return false;
        } catch (error) {
            console.error('[MTF] Analysis failed:', error);
            showError('MTF analizi başarısız: ' + error.message);
            return false;
        }
    }

    render() {
        if (!this.currentData) return;

        const data = this.currentData;
        const container = document.getElementById('mtfResultsContainer');
        if (!container) return;

        if (data.error) {
            container.innerHTML = `<div class="text-danger text-center">${data.error}</div>`;
            return;
        }

        const decision = data.decision;
        const confluence = data.confluence;

        const directionIcon = decision.direction === 'BUY' ? '🟢' : decision.direction === 'SELL' ? '🔴' : '⚪';
        const confidenceColor = decision.confidence === 'HIGH' ? 'success' : decision.confidence === 'MEDIUM' ? 'warning' : 'secondary';

        let html = `
            <!-- Decision Header -->
            <div class="mtf-decision-card ${decision.action !== 'WAIT' ? 'mtf-active' : ''}">
                <div class="mtf-decision-icon">${directionIcon}</div>
                <div class="mtf-decision-info">
                    <div class="mtf-decision-action">${decision.advice_tr}</div>
                    <div class="mtf-decision-meta">
                        <span class="badge badge-${confidenceColor}">${decision.confidence} Güven</span>
                        <span class="text-secondary">${confluence.percentage}% Confluence</span>
                    </div>
                </div>
            </div>

            <!-- Timeframe Cards -->
            <div class="mtf-tf-grid">
                ${this._renderTimeframeCard('HTF', data.timeframes.htf, data.htf_analysis)}
                ${this._renderTimeframeCard('MTF', data.timeframes.mtf, data.mtf_analysis)}
                ${this._renderTimeframeCard('LTF', data.timeframes.ltf, data.ltf_analysis)}
            </div>

            <!-- Confluence Factors -->
            <div class="mtf-factors-card">
                <h4>✅ Confluence Faktörleri</h4>
                <ul class="mtf-factors-list">
                    ${confluence.factors.map(f => `<li>${f}</li>`).join('')}
                </ul>
            </div>

            <!-- Suggested Levels -->
            ${decision.suggested_sl || decision.suggested_tp ? `
                <div class="mtf-levels-card">
                    <div class="mtf-level">
                        <span class="mtf-level-label">🎯 TP</span>
                        <span class="mtf-level-value">${decision.suggested_tp?.toFixed(5) || 'N/A'}</span>
                    </div>
                    <div class="mtf-level">
                        <span class="mtf-level-label">🛑 SL</span>
                        <span class="mtf-level-value">${decision.suggested_sl?.toFixed(5) || 'N/A'}</span>
                    </div>
                </div>
            ` : ''}
        `;

        container.innerHTML = html;
    }

    _renderTimeframeCard(label, tfName, analysis) {
        const trendIcon = analysis.trend.direction === 'BULLISH' ? '📈' :
            analysis.trend.direction === 'BEARISH' ? '📉' : '➡️';
        const trendClass = analysis.trend.direction === 'BULLISH' ? 'text-success' :
            analysis.trend.direction === 'BEARISH' ? 'text-danger' : 'text-secondary';

        return `
            <div class="mtf-tf-card">
                <div class="mtf-tf-header">
                    <span class="mtf-tf-label">${label}</span>
                    <span class="mtf-tf-name">${tfName}</span>
                </div>
                <div class="mtf-tf-trend ${trendClass}">
                    ${trendIcon} ${analysis.trend.direction}
                </div>
                <div class="mtf-tf-details">
                    <div>RSI: ${analysis.rsi?.toFixed(1)}</div>
                    <div>Zone: ${analysis.price_position.zone_name}</div>
                    <div>Struct: ${analysis.structure.type}</div>
                </div>
            </div>
        `;
    }
}

// ============================================
// DRAWDOWN RECOVERY PLANNER
// ============================================

class RecoveryPlanner {
    constructor() {
        this.currentPlan = null;
    }

    async loadPlan(initialBalance = null, peakBalance = null) {
        try {
            const params = {
                action: 'get_recovery_plan'
            };
            if (initialBalance) params.initial_balance = initialBalance;
            if (peakBalance) params.peak_balance = peakBalance;

            const response = await mt5Connector.sendMessage(params);

            if (response && response.data) {
                this.currentPlan = response.data;
                this.render();
                return true;
            }
            return false;
        } catch (error) {
            console.error('[Recovery] Plan failed:', error);
            showError('Recovery planı yüklenemedi: ' + error.message);
            return false;
        }
    }

    render() {
        if (!this.currentPlan) return;

        const plan = this.currentPlan;
        const container = document.getElementById('recoveryPlanContainer');
        if (!container) return;

        if (plan.error) {
            container.innerHTML = `<div class="text-danger text-center">${plan.error}</div>`;
            return;
        }

        const state = plan.current_state;
        const risk = plan.risk_status;
        const metrics = plan.recovery_metrics;
        const projection = plan.projection;

        const urgencyColors = {
            low: 'success',
            medium: 'warning',
            high: 'danger',
            critical: 'danger'
        };

        let html = `
            <!-- Status Badge -->
            <div class="recovery-status-card recovery-${risk.urgency}">
                <div class="recovery-status-icon">${risk.status_tr.split(' ')[0]}</div>
                <div class="recovery-status-info">
                    <div class="recovery-status-title">${risk.status_tr.split(' ').slice(1).join(' ')}</div>
                    <div class="recovery-status-dd">${state.effective_drawdown.toFixed(2)}% Drawdown</div>
                </div>
            </div>

            <!-- Key Metrics -->
            <div class="recovery-metrics-grid">
                <div class="recovery-metric">
                    <div class="recovery-metric-label">Kayıp Miktar</div>
                    <div class="recovery-metric-value text-danger">-$${state.amount_lost.toFixed(2)}</div>
                </div>
                <div class="recovery-metric">
                    <div class="recovery-metric-label">Kalan Buffer</div>
                    <div class="recovery-metric-value">${risk.remaining_buffer_pct.toFixed(1)}%</div>
                </div>
                <div class="recovery-metric">
                    <div class="recovery-metric-label">Tahmini Trade</div>
                    <div class="recovery-metric-value">${metrics.trades_needed || 'N/A'}</div>
                </div>
                <div class="recovery-metric">
                    <div class="recovery-metric-label">Tahmini Süre</div>
                    <div class="recovery-metric-value">${metrics.recovery_time_estimate || 'N/A'}</div>
                </div>
            </div>

            <!-- Monte Carlo Projection -->
            <div class="recovery-projection-card">
                <h4>📊 Monte Carlo Projeksiyonu</h4>
                <div class="recovery-projection-bars">
                    <div class="recovery-bar-item">
                        <div class="recovery-bar-label">Recovery</div>
                        <div class="recovery-bar-container">
                            <div class="recovery-bar recovery-bar-success" style="width: ${projection.recovery_probability}%"></div>
                        </div>
                        <div class="recovery-bar-value">${projection.recovery_probability}%</div>
                    </div>
                    <div class="recovery-bar-item">
                        <div class="recovery-bar-label">Bust</div>
                        <div class="recovery-bar-container">
                            <div class="recovery-bar recovery-bar-danger" style="width: ${projection.bust_probability}%"></div>
                        </div>
                        <div class="recovery-bar-value">${projection.bust_probability}%</div>
                    </div>
                </div>
            </div>

            <!-- Recommendations -->
            <div class="recovery-recs-card">
                <h4>💡 Öneriler</h4>
                <div class="recovery-recs-list">
                    ${plan.recommendations.map(rec => `
                        <div class="recovery-rec-item recovery-rec-${rec.type}">
                            <span class="recovery-rec-icon">${rec.icon}</span>
                            <div class="recovery-rec-content">
                                <div class="recovery-rec-title">${rec.title}</div>
                                <div class="recovery-rec-desc">${rec.description}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        container.innerHTML = html;
    }
}

// Create global instances
const mtfAnalyzer = new MTFAnalyzer();
const recoveryPlanner = new RecoveryPlanner();

// Global functions
window.runMTFAnalysis = function (symbol, preset) {
    if (!symbol) {
        symbol = document.getElementById('mtfSymbol')?.value || 'EURUSD';
    }
    if (!preset) {
        preset = document.getElementById('mtfPreset')?.value || 'intraday';
    }
    mtfAnalyzer.analyze(symbol, preset);
};

window.loadRecoveryPlan = function () {
    const initial = parseFloat(document.getElementById('recoveryInitialBalance')?.value) || null;
    const peak = parseFloat(document.getElementById('recoveryPeakBalance')?.value) || null;
    recoveryPlanner.loadPlan(initial, peak);
};
