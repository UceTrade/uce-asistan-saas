/**
 * Dashboard - UI updates and chart management
 */

class Dashboard {
    constructor() {
        this.equityChart = null;
        this.equityData = [];
        this.maxDataPoints = 50;
        this.initCharts();
    }

    /**
     * Initialize charts
     */
    initCharts() {
        const ctx = document.getElementById('equityChart');
        if (!ctx) return;

        this.equityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Equity',
                    data: [],
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#a0aec0',
                            callback: function (value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#a0aec0'
                        }
                    }
                }
            }
        });
    }

    /**
     * Update account overview stats
     */
    updateAccountStats(accountData) {
        // Balance
        setText('statBalance', formatCurrency(accountData.balance || 0));

        // Equity
        setText('statEquity', formatCurrency(accountData.equity || 0));

        // Profit/Loss
        const profit = accountData.profit || 0;
        const profitEl = document.getElementById('statProfit');
        if (profitEl) {
            profitEl.textContent = formatCurrency(profit);
            profitEl.className = `stat-value ${profit >= 0 ? 'stat-positive' : 'stat-negative'}`;
        }

        // Daily P/L
        const dailyProfit = accountData.daily_profit || 0;
        const dailyProfitEl = document.getElementById('statDailyProfit');
        if (dailyProfitEl) {
            dailyProfitEl.textContent = formatCurrency(dailyProfit);
            dailyProfitEl.className = `stat-value ${dailyProfit >= 0 ? 'stat-positive' : 'stat-negative'}`;
        }
    }

    /**
     * Update performance metrics
     */
    updatePerformanceMetrics(accountData) {
        setText('openPositions', accountData.positions_count || 0);
        setText('marginLevel', formatPercent(accountData.margin_level || 0));
        setText('freeMargin', formatCurrency(accountData.margin_free || 0));
        setText('usedMargin', formatCurrency(accountData.margin || 0));
    }

    /**
     * Update positions list
     */
    updatePositionsList(positions) {
        const container = document.getElementById('positionsList');
        if (!container) return;

        if (!positions || positions.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No open positions</div>';
            return;
        }

        // Performance Fix: Use DocumentFragment for large lists if needed, 
        // but for positions (usually < 20), batch mapping is fine.
        // We add a simple check to avoid unnecessary full-DOM rewrites if data hasn't changed.
        const currentContent = container.getAttribute('data-pos-hash');
        const newHash = positions.map(p => `${p.symbol}:${p.profit}:${p.price_current}`).join('|');

        if (currentContent === newHash) return; // Skip update if visual data is same

        const html = positions.map(pos => {
            const isProfit = pos.profit >= 0;
            return `
                <div class="glass-card mb-sm" style="padding: var(--space-sm);">
                    <div class="flex justify-between items-center">
                        <div>
                            <div style="font-weight: 600;">${pos.symbol}</div>
                            <div class="text-sm text-secondary">${pos.type} ${pos.volume} lots</div>
                        </div>
                        <div class="text-right">
                            <div class="${isProfit ? 'stat-positive' : 'stat-negative'}" style="font-weight: 600;">
                                ${formatCurrency(pos.profit)}
                            </div>
                            <div class="text-sm text-secondary">${pos.price_current.toFixed(5)}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        requestAnimationFrame(() => {
            container.innerHTML = html;
            container.setAttribute('data-pos-hash', newHash);
        });
    }

    /**
     * Update equity chart
     */
    updateEquityChart(equity) {
        if (!this.equityChart) return;

        const now = new Date();
        const timeLabel = now.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });

        // Add new data point
        this.equityData.push({ time: timeLabel, value: equity });

        // Keep only last N points
        if (this.equityData.length > this.maxDataPoints) {
            this.equityData.shift();
        }

        // Update chart
        this.equityChart.data.labels = this.equityData.map(d => d.time);
        this.equityChart.data.datasets[0].data = this.equityData.map(d => d.value);
        this.equityChart.update('none'); // Update without animation for performance
    }

    /**
     * Update portfolio view
     */
    updatePortfolioView(portfolioData) {
        setText('portfolioBalance', formatCurrency(portfolioData.total_balance || 0));
        setText('portfolioEquity', formatCurrency(portfolioData.total_equity || 0));

        const totalProfit = portfolioData.total_profit || 0;
        const profitEl = document.getElementById('portfolioProfit');
        if (profitEl) {
            profitEl.textContent = formatCurrency(totalProfit);
            profitEl.className = `stat-value ${totalProfit >= 0 ? 'stat-positive' : 'stat-negative'}`;
        }

        setText('portfolioAccounts', portfolioData.accounts_count || 0);

        // Update accounts comparison
        this.updateAccountsComparison(portfolioData.accounts || []);
    }

    /**
     * Update accounts comparison table
     */
    updateAccountsComparison(accounts) {
        const container = document.getElementById('accountsComparison');
        if (!container) return;

        if (!accounts || accounts.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No accounts added yet</div>';
            return;
        }

        const html = `
            <div class="grid grid-3 gap-md">
                ${accounts.map(acc => {
            const profit = acc.profit || 0;
            const dailyProfit = acc.daily_profit || 0;
            return `
                        <div class="glass-card">
                            <h3 class="mb-sm">${acc.account_id}</h3>
                            <div class="mb-sm">
                                <div class="text-sm text-secondary">Balance</div>
                                <div class="text-lg">${formatCurrency(acc.balance)}</div>
                            </div>
                            <div class="mb-sm">
                                <div class="text-sm text-secondary">Total P/L</div>
                                <div class="text-lg ${profit >= 0 ? 'stat-positive' : 'stat-negative'}">
                                    ${formatCurrency(profit)}
                                </div>
                            </div>
                            <div class="mb-sm">
                                <div class="text-sm text-secondary">Daily P/L</div>
                                <div class="text-lg ${dailyProfit >= 0 ? 'stat-positive' : 'stat-negative'}">
                                    ${formatCurrency(dailyProfit)}
                                </div>
                            </div>
                            <div>
                                <div class="text-sm text-secondary">Drawdown</div>
                                <div class="text-lg">${formatPercent(acc.current_drawdown || 0)}</div>
                            </div>
                        </div>
                    `;
        }).join('')}
            </div>
        `;

        container.innerHTML = html;
    }

}

// Create global instance
const dashboard = new Dashboard();
