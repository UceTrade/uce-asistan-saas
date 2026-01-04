/**
 * Signal Confluence Finder - Frontend
 * Professional UI for multi-strategy confluence detection
 */

class ConfluenceFinder {
    constructor() {
        this.selectedStrategies = [];
        this.confluenceResults = null;
    }

    /**
     * Initialize confluence finder
     */
    init() {
        this.loadAvailableStrategies();
        this.setupEventListeners();
    }

    /**
     * Load available strategies (templates + saved)
     */
    async loadAvailableStrategies() {
        try {
            // Load templates
            const templatesResponse = await mt5Connector.sendMessage({
                action: 'get_templates'
            });

            if (templatesResponse && templatesResponse.data) {
                this.renderTemplateCheckboxes(templatesResponse.data);
            }

            // Load saved strategies
            const savedResponse = await mt5Connector.sendMessage({
                action: 'get_strategies'
            });

            if (savedResponse && savedResponse.data) {
                this.renderSavedCheckboxes(savedResponse.data);
            }

        } catch (error) {
            console.error('[CONFLUENCE] Error loading strategies:', error);
        }
    }

    /**
     * Render template checkboxes
     */
    renderTemplateCheckboxes(templates) {
        const container = document.getElementById('confluenceTemplates');
        if (!container) return;

        container.innerHTML = templates.map(template => `
            <label class="confluence-checkbox">
                <input type="checkbox" 
                       value="${template.id}" 
                       data-type="template"
                       data-name="${template.name}"
                       onchange="confluenceFinder.toggleStrategy(this)">
                <span>${template.category} ${template.name}</span>
            </label>
        `).join('');
    }

    /**
     * Render saved strategy checkboxes
     */
    renderSavedCheckboxes(strategies) {
        const container = document.getElementById('confluenceSaved');
        if (!container) return;

        if (strategies.length === 0) {
            container.innerHTML = '<p class="text-secondary text-sm">Henüz kayıtlı strateji yok</p>';
            return;
        }

        container.innerHTML = strategies.map(strategy => `
            <label class="confluence-checkbox">
                <input type="checkbox" 
                       value="${strategy.id}" 
                       data-type="saved"
                       data-name="${strategy.name}"
                       onchange="confluenceFinder.toggleStrategy(this)">
                <span>${strategy.name} <small class="text-secondary">(${strategy.created_at})</small></span>
            </label>
        `).join('');
    }

    /**
     * Toggle strategy selection
     */
    toggleStrategy(checkbox) {
        const strategyId = checkbox.value;
        const strategyType = checkbox.dataset.type;
        const strategyName = checkbox.dataset.name;

        if (checkbox.checked) {
            // Add to selection
            this.selectedStrategies.push({
                id: strategyId,
                type: strategyType,
                name: strategyName
            });
        } else {
            // Remove from selection
            this.selectedStrategies = this.selectedStrategies.filter(
                s => !(s.id === strategyId && s.type === strategyType)
            );
        }

        this.updateSelectedCount();
    }

    /**
     * Update selected count display
     */
    updateSelectedCount() {
        const countElement = document.getElementById('confluenceSelectedCount');
        if (countElement) {
            countElement.textContent = this.selectedStrategies.length;
        }

        // Enable/disable find button
        const findButton = document.getElementById('findConfluencesBtn');
        if (findButton) {
            findButton.disabled = this.selectedStrategies.length < 2;
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Min agreement slider
        const slider = document.getElementById('minAgreementSlider');
        const valueDisplay = document.getElementById('agreementValue');

        if (slider && valueDisplay) {
            slider.addEventListener('input', (e) => {
                valueDisplay.textContent = e.target.value + '%';
            });
        }
    }

    /**
     * Find confluences
     */
    async findConfluences() {
        if (this.selectedStrategies.length < 2) {
            showError('En az 2 strateji seçmelisiniz');
            return;
        }

        const minAgreement = document.getElementById('minAgreementSlider').value / 100;
        const symbol = document.getElementById('confluenceSymbol')?.value || 'EURUSD';
        const timeframe = document.getElementById('confluenceTimeframe')?.value || 'H1';

        // Show loading
        const resultsContainer = document.getElementById('confluenceResults');
        resultsContainer.style.display = 'block';
        resultsContainer.innerHTML = `
            <div class="text-center p-lg">
                <div class="spinner"></div>
                <p class="mt-md">Analyzing ${this.selectedStrategies.length} strategies...</p>
                <p class="text-secondary text-sm">This may take a few moments</p>
            </div>
        `;

        try {
            console.log('[CONFLUENCE] Sending request:', {
                strategies: this.selectedStrategies,
                min_agreement: minAgreement,
                symbol,
                timeframe
            });

            const response = await mt5Connector.sendMessage({
                action: 'find_confluences',
                strategies: this.selectedStrategies,
                min_agreement: minAgreement,
                symbol: symbol,
                timeframe: timeframe,
                bars: 500
            });

            console.log('[CONFLUENCE] Response:', response);

            if (response.error) {
                showError('Confluence Error: ' + response.error);
                resultsContainer.innerHTML = `
                    <div class="alert alert-error">
                        <strong>Error:</strong> ${response.error}
                    </div>
                `;
                return;
            }

            this.confluenceResults = response;
            this.displayResults(response);

        } catch (error) {
            console.error('[CONFLUENCE] Error:', error);
            showError('Failed to find confluences: ' + error.message);
            resultsContainer.innerHTML = `
                <div class="alert alert-error">
                    <strong>Error:</strong> ${error.message}
                </div>
            `;
        }
    }

    /**
     * Display confluence results
     */
    displayResults(response) {
        const container = document.getElementById('confluenceResults');
        const confluences = response.confluences || [];
        const summary = response.execution_summary || {};

        if (confluences.length === 0) {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <strong>No Confluences Found</strong>
                    <p>Try lowering the minimum agreement threshold or selecting more strategies.</p>
                </div>
            `;
            return;
        }

        // Build results HTML
        let html = `
            <div class="confluence-summary mb-lg">
                <h3>📊 Confluence Analysis Results</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">${confluences.length}</div>
                        <div class="stat-label">Confluences Found</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${summary.successful}/${summary.total_strategies}</div>
                        <div class="stat-label">Strategies Executed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${this.getStrongestConfluence(confluences)}</div>
                        <div class="stat-label">Strongest Signal</div>
                    </div>
                </div>
            </div>

            <div class="confluence-timeline">
                <h3>🎯 Confluence Timeline</h3>
        `;

        // Group by strength
        const veryStrong = confluences.filter(c => c.strength === 'VERY_STRONG');
        const strong = confluences.filter(c => c.strength === 'STRONG');
        const medium = confluences.filter(c => c.strength === 'MEDIUM');

        if (veryStrong.length > 0) {
            html += this.renderConfluenceGroup('VERY STRONG 🔥', veryStrong, 'very-strong');
        }

        if (strong.length > 0) {
            html += this.renderConfluenceGroup('STRONG 💪', strong, 'strong');
        }

        if (medium.length > 0) {
            html += this.renderConfluenceGroup('MEDIUM 👍', medium, 'medium');
        }

        html += '</div>';

        container.innerHTML = html;
        showSuccess(`Found ${confluences.length} confluence signals!`);
    }

    /**
     * Render confluence group
     */
    renderConfluenceGroup(title, confluences, className) {
        return `
            <div class="confluence-group ${className} mb-md">
                <h4>${title} (${confluences.length})</h4>
                ${confluences.map(conf => this.renderConfluenceCard(conf)).join('')}
            </div>
        `;
    }

    /**
     * Render single confluence card
     */
    renderConfluenceCard(confluence) {
        const signalIcon = confluence.signal === 'BUY' ? '🟢' : '🔴';
        const agreementPct = (confluence.agreement * 100).toFixed(0);

        return `
            <div class="confluence-card">
                <div class="conf-header">
                    <span class="conf-signal">${signalIcon} ${confluence.signal}</span>
                    <span class="conf-time">${this.formatTimestamp(confluence.timestamp)}</span>
                </div>
                <div class="conf-body">
                    <div class="conf-agreement">
                        <strong>Agreement: ${agreementPct}%</strong>
                        <span class="text-secondary">(${confluence.agreeing_count}/${confluence.total_count} strategies)</span>
                    </div>
                    <div class="conf-strategies mt-sm">
                        <details>
                            <summary class="text-sm">✅ Agreeing Strategies (${confluence.agreeing_count})</summary>
                            <ul class="strategy-list">
                                ${confluence.strategies_agreeing.map(s => `<li>${s}</li>`).join('')}
                            </ul>
                        </details>
                        ${confluence.strategies_disagreeing.length > 0 ? `
                            <details class="mt-xs">
                                <summary class="text-sm">❌ Disagreeing (${confluence.strategies_disagreeing.length})</summary>
                                <ul class="strategy-list">
                                    ${confluence.strategies_disagreeing.map(s => `<li>${s}</li>`).join('')}
                                </ul>
                            </details>
                        ` : ''}
                    </details>
                    </div>
                </div>
                <div class="conf-footer">
                    <span class="conf-strength">${confluence.strength_icon} ${confluence.strength.replace('_', ' ')}</span>
                </div>
            </div>
        `;
    }

    /**
     * Get strongest confluence percentage
     */
    getStrongestConfluence(confluences) {
        if (confluences.length === 0) return '0%';
        const strongest = Math.max(...confluences.map(c => c.agreement));
        return (strongest * 100).toFixed(0) + '%';
    }

    /**
     * Format timestamp
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('tr-TR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Initialize
const confluenceFinder = new ConfluenceFinder();

// Initialize when DOM is ready AND WebSocket is connected
document.addEventListener('DOMContentLoaded', () => {
    // Wait for WebSocket connection
    const checkConnection = setInterval(() => {
        if (mt5Connector && mt5Connector.connected) {
            clearInterval(checkConnection);
            confluenceFinder.init();
            console.log('[CONFLUENCE] Initialized after WebSocket connection');
        }
    }, 500); // Check every 500ms

    // Timeout after 10 seconds
    setTimeout(() => {
        clearInterval(checkConnection);
        console.warn('[CONFLUENCE] WebSocket connection timeout - init skipped');
    }, 10000);
});

// Export for global access
window.confluenceFinder = confluenceFinder;
window.findConfluences = () => confluenceFinder.findConfluences();
