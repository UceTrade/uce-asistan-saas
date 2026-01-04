/**
 * Journal Analytics - Frontend Controller
 * Advanced trading performance analytics and visualization
 */

class JournalAnalyticsController {
    constructor() {
        this.data = null;
        this.charts = {};
    }

    /**
     * Load analytics data from backend
     */
    async loadAnalytics(days = 30) {
        try {
            const response = await mt5Connector.sendMessage({
                action: 'get_journal_analytics',
                days: days
            });

            if (response && response.data) {
                this.data = response.data;
                this.renderAnalytics();
                return true;
            }
            return false;
        } catch (error) {
            console.error('[JournalAnalytics] Error loading analytics:', error);
            showError('Analitik veriler yüklenemedi: ' + error.message);
            return false;
        }
    }

    /**
     * Render all analytics components
     */
    renderAnalytics() {
        if (!this.data) return;

        this.renderSummaryCards();
        this.renderHourlyChart();
        this.renderDailyChart();
        this.renderSymbolTable();
        this.renderEmotionChart();
        this.renderStreakInfo();
        this.renderRecommendations();
    }

    /**
     * Render summary stats cards
     */
    renderSummaryCards() {
        const summary = this.data.summary || {};

        setText('analyticsWinRate', `${summary.win_rate || 0}%`);
        setText('analyticsProfitFactor', summary.profit_factor?.toFixed(2) || '0.00');
        setText('analyticsNetProfit', `$${(summary.net_profit || 0).toFixed(2)}`);
        setText('analyticsExpectancy', `$${(summary.expectancy || 0).toFixed(2)}`);
        setText('analyticsTotalTrades', summary.total_trades || 0);
        setText('analyticsAvgTrade', `$${(summary.avg_trade || 0).toFixed(2)}`);
    }

    /**
     * Render hourly performance bar chart
     */
    renderHourlyChart() {
        const container = document.getElementById('hourlyChartContainer');
        if (!container) return;

        const hourly = this.data.hourly_performance || [];

        if (hourly.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Henüz yeterli veri yok</p>';
            return;
        }

        // Create horizontal bar chart representation
        let html = '<div class="hourly-chart">';

        const maxProfit = Math.max(...hourly.map(h => Math.abs(h.net_profit)), 1);

        hourly.forEach(hour => {
            const isPositive = hour.net_profit >= 0;
            const barWidth = (Math.abs(hour.net_profit) / maxProfit * 100).toFixed(1);
            const barClass = isPositive ? 'bar-positive' : 'bar-negative';

            html += `
                <div class="hour-row">
                    <div class="hour-label">${hour.hour_label}</div>
                    <div class="hour-bar-container">
                        <div class="hour-bar ${barClass}" style="width: ${barWidth}%"></div>
                    </div>
                    <div class="hour-stats">
                        <span class="${isPositive ? 'text-success' : 'text-danger'}">
                            ${isPositive ? '+' : ''}$${hour.net_profit.toFixed(2)}
                        </span>
                        <span class="text-secondary text-sm">(${hour.win_rate}%)</span>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Render daily performance chart
     */
    renderDailyChart() {
        const container = document.getElementById('dailyChartContainer');
        if (!container) return;

        const daily = this.data.daily_performance || [];

        if (daily.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Henüz yeterli veri yok</p>';
            return;
        }

        let html = '<div class="daily-chart">';

        daily.forEach(day => {
            const isPositive = day.net_profit >= 0;
            const winRateClass = day.win_rate >= 50 ? 'badge-success' : 'badge-danger';

            html += `
                <div class="day-card ${isPositive ? 'day-positive' : 'day-negative'}">
                    <div class="day-name">${day.day_name_tr}</div>
                    <div class="day-profit ${isPositive ? 'text-success' : 'text-danger'}">
                        ${isPositive ? '+' : ''}$${day.net_profit.toFixed(2)}
                    </div>
                    <div class="day-meta">
                        <span class="badge ${winRateClass}">${day.win_rate}%</span>
                        <span class="text-secondary text-sm">${day.trade_count} işlem</span>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Render symbol performance table
     */
    renderSymbolTable() {
        const container = document.getElementById('symbolTableContainer');
        if (!container) return;

        const symbols = this.data.symbol_performance || [];

        if (symbols.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Henüz yeterli veri yok</p>';
            return;
        }

        let html = `
            <table class="analytics-table">
                <thead>
                    <tr>
                        <th>Sembol</th>
                        <th>İşlem</th>
                        <th>Kazanma %</th>
                        <th>Net K/Z</th>
                    </tr>
                </thead>
                <tbody>
        `;

        symbols.forEach((symbol, index) => {
            const isPositive = symbol.net_profit >= 0;
            const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '';

            html += `
                <tr>
                    <td><strong>${medal} ${symbol.symbol}</strong></td>
                    <td>${symbol.trade_count}</td>
                    <td>
                        <span class="badge ${symbol.win_rate >= 50 ? 'badge-success' : 'badge-danger'}">
                            ${symbol.win_rate}%
                        </span>
                    </td>
                    <td class="${isPositive ? 'text-success' : 'text-danger'}">
                        ${isPositive ? '+' : ''}$${symbol.net_profit.toFixed(2)}
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    /**
     * Render emotion analysis chart
     */
    renderEmotionChart() {
        const container = document.getElementById('emotionChartContainer');
        if (!container) return;

        const emotions = this.data.emotion_analysis || [];

        if (emotions.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Duygu etiketi eklenmemiş</p>';
            return;
        }

        let html = '<div class="emotion-grid">';

        emotions.forEach(emotion => {
            const isPositive = emotion.net_profit >= 0;
            const performanceClass = emotion.win_rate >= 50 ? 'emotion-good' : 'emotion-bad';

            html += `
                <div class="emotion-card ${performanceClass}">
                    <div class="emotion-icon">${emotion.emotion_label}</div>
                    <div class="emotion-stats">
                        <div class="emotion-win-rate">${emotion.win_rate}%</div>
                        <div class="emotion-profit ${isPositive ? 'text-success' : 'text-danger'}">
                            ${isPositive ? '+' : ''}$${emotion.net_profit.toFixed(2)}
                        </div>
                        <div class="text-secondary text-sm">${emotion.trade_count} işlem</div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Render streak information
     */
    renderStreakInfo() {
        const container = document.getElementById('streakContainer');
        if (!container) return;

        const streaks = this.data.streaks || {};
        const risk = this.data.risk_metrics || {};

        const currentStreak = streaks.current || 0;
        const streakType = currentStreak > 0 ? 'win' : currentStreak < 0 ? 'loss' : 'neutral';
        const streakIcon = streakType === 'win' ? '🔥' : streakType === 'loss' ? '❄️' : '➖';
        const streakClass = streakType === 'win' ? 'text-success' : streakType === 'loss' ? 'text-danger' : '';

        let html = `
            <div class="streak-grid">
                <div class="streak-item">
                    <div class="streak-label">Mevcut Seri</div>
                    <div class="streak-value ${streakClass}">
                        ${streakIcon} ${Math.abs(currentStreak)} ${streakType === 'win' ? 'Kazanç' : streakType === 'loss' ? 'Kayıp' : '-'}
                    </div>
                </div>
                <div class="streak-item">
                    <div class="streak-label">En İyi Kazanç Serisi</div>
                    <div class="streak-value text-success">🏆 ${streaks.best_win || 0}</div>
                </div>
                <div class="streak-item">
                    <div class="streak-label">En Kötü Kayıp Serisi</div>
                    <div class="streak-value text-danger">💀 ${streaks.worst_loss || 0}</div>
                </div>
                <div class="streak-item">
                    <div class="streak-label">Max Drawdown</div>
                    <div class="streak-value">$${(risk.max_drawdown || 0).toFixed(2)}</div>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    /**
     * Render AI recommendations
     */
    renderRecommendations() {
        const container = document.getElementById('recommendationsContainer');
        if (!container) return;

        const recommendations = this.data.recommendations || [];

        if (recommendations.length === 0) {
            container.innerHTML = '<p class="text-muted">Henüz öneri yok</p>';
            return;
        }

        let html = '<div class="recommendations-list">';

        recommendations.forEach(rec => {
            const typeClass = rec.type === 'success' ? 'rec-success' :
                rec.type === 'danger' ? 'rec-danger' :
                    rec.type === 'warning' ? 'rec-warning' : 'rec-info';

            html += `
                <div class="recommendation-item ${typeClass}">
                    <span class="rec-icon">${rec.icon || '💡'}</span>
                    <div class="rec-content">
                        <div class="rec-category">${rec.category}</div>
                        <div class="rec-message">${rec.message}</div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }
}

// Create global instance
const journalAnalytics = new JournalAnalyticsController();

// Global function for button
window.loadJournalAnalytics = function (days = 30) {
    journalAnalytics.loadAnalytics(days);
};
