/**
 * Risk Manager - Risk calculation and alert system
 */

class RiskManager {
    constructor() {
        this.propFirmRules = {
            maxDrawdown: 10.0,  // %
            dailyLimit: 5.0     // %
        };
        this.loadSettings();
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        const settings = loadFromStorage('propFirmRules');
        if (settings) {
            this.propFirmRules = settings;
        }
    }

    /**
     * Save settings to localStorage
     */
    saveSettings() {
        saveToStorage('propFirmRules', this.propFirmRules);
    }

    /**
     * Update prop firm rules
     */
    updateRules(maxDrawdown, dailyLimit) {
        this.propFirmRules.maxDrawdown = parseFloat(maxDrawdown);
        this.propFirmRules.dailyLimit = parseFloat(dailyLimit);
        this.saveSettings();
    }

    /**
     * Calculate risk metrics for account
     */
    calculateRiskMetrics(accountData) {
        const balance = accountData.balance || 0;
        const equity = accountData.equity || 0;
        const dailyProfit = accountData.daily_profit || 0;
        const currentDrawdown = accountData.current_drawdown || 0;

        // Calculate drawdown usage
        const drawdownUsed = (currentDrawdown / this.propFirmRules.maxDrawdown) * 100;

        // Calculate daily risk usage
        const dailyLoss = Math.abs(Math.min(dailyProfit, 0));
        const dailyLossPercent = balance > 0 ? (dailyLoss / balance) * 100 : 0;
        const dailyRiskUsed = (dailyLossPercent / this.propFirmRules.dailyLimit) * 100;

        // Determine risk level
        const riskLevel = this.determineRiskLevel(drawdownUsed, dailyRiskUsed);

        // Calculate remaining risk
        const remainingDrawdown = this.propFirmRules.maxDrawdown - currentDrawdown;
        const remainingDailyRisk = (this.propFirmRules.dailyLimit * balance / 100) - dailyLoss;

        return {
            currentDrawdown,
            maxDrawdownLimit: this.propFirmRules.maxDrawdown,
            drawdownUsed,
            dailyProfit,
            dailyLoss,
            dailyLossPercent,
            dailyLimit: this.propFirmRules.dailyLimit,
            dailyRiskUsed,
            riskLevel,
            remainingDrawdown,
            remainingDailyRisk: Math.max(0, remainingDailyRisk)
        };
    }

    /**
     * Determine risk level based on usage
     */
    determineRiskLevel(drawdownUsed, dailyRiskUsed) {
        const maxUsage = Math.max(drawdownUsed, dailyRiskUsed);

        if (maxUsage >= 95) return 'danger';
        if (maxUsage >= 85) return 'warning';
        if (maxUsage >= 70) return 'caution';
        return 'safe';
    }

    /**
     * Check if should alert
     */
    shouldAlert(riskLevel, previousRiskLevel) {
        const levels = ['safe', 'caution', 'warning', 'danger'];
        const currentIndex = levels.indexOf(riskLevel);
        const previousIndex = levels.indexOf(previousRiskLevel || 'safe');

        // Alert if risk level increased
        return currentIndex > previousIndex;
    }

    /**
     * Get alert message for risk level
     */
    getAlertMessage(riskLevel, metrics) {
        const messages = {
            caution: `⚠️ Dikkat: Maksimum düşüş limitinin %${metrics.drawdownUsed.toFixed(1)}'ini kullandınız. Dikkatli işlem yapın.`,
            warning: `🟠 Uyarı: Yüksek risk! %${metrics.drawdownUsed.toFixed(1)} düşüş kullanıldı. İşlem büyüklüklerini azaltmayı düşünün.`,
            danger: `🔴 TEHLİKE: Kritik risk seviyesi! %${metrics.drawdownUsed.toFixed(1)} düşüş. İşlemleri derhal durdurun!`
        };

        return messages[riskLevel] || null;
    }

    /**
     * Calculate position size based on risk
     */
    calculatePositionSize(accountBalance, riskPercent, stopLossPips, pipValue = 10) {
        const riskAmount = accountBalance * (riskPercent / 100);
        const lotSize = riskAmount / (stopLossPips * pipValue);

        // Round to 2 decimals
        return Math.round(lotSize * 100) / 100;
    }

    /**
     * Validate trade against rules
     */
    validateTrade(accountData, proposedLotSize, stopLossPips, pipValue = 10) {
        const metrics = this.calculateRiskMetrics(accountData);

        // Calculate potential loss
        const potentialLoss = proposedLotSize * stopLossPips * pipValue;
        const potentialLossPercent = (potentialLoss / accountData.balance) * 100;

        // Check if trade would exceed limits
        const wouldExceedDrawdown = (metrics.currentDrawdown + potentialLossPercent) > this.propFirmRules.maxDrawdown;
        const wouldExceedDailyLimit = (metrics.dailyLossPercent + potentialLossPercent) > this.propFirmRules.dailyLimit;

        const valid = !wouldExceedDrawdown && !wouldExceedDailyLimit;

        return {
            valid,
            potentialLoss,
            potentialLossPercent,
            wouldExceedDrawdown,
            wouldExceedDailyLimit,
            message: valid ? 'İşlem risk limitleri dahilinde' : 'İşlem risk limitlerini aşacak',
            recommendations: this.getTradeRecommendations(metrics, potentialLossPercent)
        };
    }

    /**
     * Get trade recommendations
     */
    getTradeRecommendations(metrics, potentialLossPercent) {
        const recommendations = [];

        if (metrics.riskLevel === 'danger') {
            recommendations.push('🔴 Yeni işlem açmayın - risk kritik seviyede');
            recommendations.push('Mevcut pozisyonları kapatmayı düşünün');
        } else if (metrics.riskLevel === 'warning') {
            recommendations.push('🟠 Pozisyon büyüklüğünü %50 azaltın');
            recommendations.push('Sadece yüksek olasılıklı kurulumları değerlendirin');
        } else if (metrics.riskLevel === 'caution') {
            recommendations.push('🟡 Pozisyon büyüklüğünü %25 azaltmayı düşünün');
            recommendations.push('İşlem girişlerinde seçici olun');
        } else {
            const maxSafeRisk = Math.min(
                metrics.remainingDrawdown / 2,
                metrics.dailyLimit / 2
            );
            recommendations.push(`🟢 İşlem başına %${maxSafeRisk.toFixed(2)} riske kadar güvenli`);
        }

        return recommendations;
    }

    /**
     * Update UI with risk metrics
     */
    updateRiskUI(metrics) {
        // Update drawdown bar
        const drawdownBar = document.getElementById('drawdownBar');
        const drawdownPercent = document.getElementById('drawdownPercent');

        if (drawdownBar && drawdownPercent) {
            drawdownBar.style.width = `${Math.min(metrics.drawdownUsed, 100)}%`;
            drawdownPercent.textContent = `${metrics.currentDrawdown.toFixed(2)}% / ${metrics.maxDrawdownLimit}%`;
        }

        // Update daily risk bar
        const dailyRiskBar = document.getElementById('dailyRiskBar');
        const dailyRiskPercent = document.getElementById('dailyRiskPercent');

        if (dailyRiskBar && dailyRiskPercent) {
            dailyRiskBar.style.width = `${Math.min(metrics.dailyRiskUsed, 100)}%`;
            dailyRiskPercent.textContent = `${metrics.dailyLossPercent.toFixed(2)}% / ${metrics.dailyLimit}%`;
        }

        // Update risk level badge
        const riskBadge = document.getElementById('riskLevelBadge');
        if (riskBadge) {
            const emoji = getRiskLevelEmoji(metrics.riskLevel);
            const text = getRiskLevelText(metrics.riskLevel);
            riskBadge.textContent = `${emoji} ${text}`;
            riskBadge.className = `badge badge-${metrics.riskLevel === 'safe' ? 'success' : metrics.riskLevel === 'danger' ? 'danger' : 'warning'}`;
        }
    }
}

// Create global instance
const riskManager = new RiskManager();

// ============================================
// PROP FIRM RULES MANAGEMENT
// ============================================

let currentPropFirm = null;

/**
 * Load prop firm rules (auto-detect or manual)
 */
async function loadPropFirmRules(firmKey = '') {
    const contentDiv = document.getElementById('propFirmContent');
    const warningsDiv = document.getElementById('propFirmWarnings');

    if (!contentDiv) return;

    contentDiv.innerHTML = `
        <div class="text-center text-muted p-md">
            <p>⏳ Kurallar yükleniyor...</p>
        </div>
    `;

    try {
        if (!window.mt5Connector || !window.mt5Connector.connected) {
            contentDiv.innerHTML = `
                <div class="text-center text-warning p-md">
                    <p>⚠️ MT5 bağlantısı yok</p>
                    <small>Sunucuya bağlandıktan sonra kurallar otomatik yüklenecek</small>
                </div>
            `;
            return;
        }

        const response = await window.mt5Connector.sendMessage({
            action: 'get_prop_firm_rules',
            firm_key: firmKey || null
        });

        if (response && response.detected) {
            currentPropFirm = response;
            displayPropFirmRules(response);

            // Update risk manager with new rules
            riskManager.propFirmRules.maxDrawdown = response.rules.max_drawdown;
            riskManager.propFirmRules.dailyLimit = response.rules.daily_drawdown;
            riskManager.saveSettings();

            // Update dropdown to show detected firm
            const select = document.getElementById('propFirmSelect');
            if (select && response.firm_key) {
                select.value = response.firm_key;
            }
        } else {
            displayNoPropFirm(response);
        }

    } catch (error) {
        console.error('[PROP FIRM] Error loading rules:', error);
        contentDiv.innerHTML = `
            <div class="text-center text-danger p-md">
                <p>❌ Hata: ${error.message}</p>
            </div>
        `;
    }
}

/**
 * Display prop firm rules in the panel
 */
function displayPropFirmRules(data) {
    const contentDiv = document.getElementById('propFirmContent');
    const warningsDiv = document.getElementById('propFirmWarnings');

    const rules = data.rules;
    const aiSummary = data.ai_summary || '';

    contentDiv.innerHTML = `
        <div class="prop-firm-header mb-md">
            <div class="flex items-center gap-md">
                <span class="text-2xl">🏦</span>
                <div>
                    <h3 class="text-primary mb-0">${data.firm_name}</h3>
                    <small class="text-secondary">Broker: ${data.broker_name || 'N/A'}</small>
                </div>
            </div>
        </div>
        
        <div class="grid grid-3 gap-md mb-md">
            <div class="prop-rule-card">
                <div class="prop-rule-label">Max Drawdown</div>
                <div class="prop-rule-value text-danger">${rules.max_drawdown}%</div>
            </div>
            <div class="prop-rule-card">
                <div class="prop-rule-label">Günlük Limit</div>
                <div class="prop-rule-value text-warning">${rules.daily_drawdown}%</div>
            </div>
            <div class="prop-rule-card">
                <div class="prop-rule-label">Kar Payı</div>
                <div class="prop-rule-value text-success">${rules.profit_split}%</div>
            </div>
        </div>
        
        <div class="grid grid-4 gap-sm mb-md text-sm">
            <div class="flex items-center gap-xs">
                <span>${rules.news_trading_allowed ? '✅' : '❌'}</span>
                <span>Haber Trading</span>
            </div>
            <div class="flex items-center gap-xs">
                <span>${rules.weekend_holding_allowed ? '✅' : '❌'}</span>
                <span>Hafta Sonu</span>
            </div>
            <div class="flex items-center gap-xs">
                <span>${rules.consistency_rule ? '⚠️' : '✅'}</span>
                <span>Tutarlılık Kuralı</span>
            </div>
            <div class="flex items-center gap-xs">
                <span>📅</span>
                <span>Min ${rules.min_trading_days} Gün</span>
            </div>
        </div>
        
        <details class="prop-firm-summary">
            <summary class="cursor-pointer text-primary mb-sm">🤖 AI Analizi ve Tavsiyeler</summary>
            <div class="ai-summary-content p-md mt-sm" style="background: rgba(0,0,0,0.2); border-radius: 8px; white-space: pre-line; line-height: 1.6; font-size: 0.9em;">
${aiSummary}
            </div>
        </details>
    `;

    // Display warnings if any
    if (data.warnings && data.warnings.length > 0) {
        warningsDiv.style.display = 'block';
        warningsDiv.innerHTML = `
            <div class="prop-firm-warnings p-md" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px;">
                <h4 class="text-warning mb-sm">⚠️ Aktif Uyarılar</h4>
                <ul class="pl-md" style="margin: 0;">
                    ${data.warnings.map(w => `<li class="text-sm mb-xs">${w}</li>`).join('')}
                </ul>
            </div>
        `;
    } else {
        warningsDiv.style.display = 'none';
    }
}

/**
 * Display when no prop firm detected
 */
function displayNoPropFirm(data) {
    const contentDiv = document.getElementById('propFirmContent');

    contentDiv.innerHTML = `
        <div class="text-center p-md">
            <p class="text-secondary mb-md">🔍 Prop firm otomatik algılanamadı</p>
            <p class="text-sm text-muted mb-md">
                Broker: ${data?.broker_name || 'Bilinmiyor'}<br>
                Server: ${data?.server_name || 'Bilinmiyor'}
            </p>
            <p class="text-sm">Yukarıdaki dropdown'dan manuel olarak seçebilirsiniz.</p>
        </div>
    `;
}

/**
 * Refresh prop firm rules
 */
function refreshPropFirmRules() {
    const select = document.getElementById('propFirmSelect');
    loadPropFirmRules(select?.value || '');
}

/**
 * Get current prop firm key
 */
function getCurrentPropFirmKey() {
    return currentPropFirm?.firm_key || null;
}

// Auto-load prop firm rules when MT5 connects
if (typeof mt5Connector !== 'undefined') {
    mt5Connector.on('account_info', () => {
        // Wait a bit for connection to stabilize then load rules
        setTimeout(() => {
            loadPropFirmRules();
        }, 1000);
    });
}

// Export functions globally
window.loadPropFirmRules = loadPropFirmRules;
window.refreshPropFirmRules = refreshPropFirmRules;
window.getCurrentPropFirmKey = getCurrentPropFirmKey;

