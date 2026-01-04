/**
 * Main Application - Core logic and event handlers
 */

// ============================================
// STATE MANAGEMENT
// ============================================

const appState = {
    accounts: new Map(),
    currentAccountId: null,
    currentView: 'dashboard', // dashboard, portfolio, backtest, or neural
    chatOpen: false,
    lastRiskLevel: new Map() // Track risk levels for alerts
};

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('UceAsistan başlatılıyor...');

    // Phase 1: Initialize Auth
    await uceAuth.init();

    if (!uceAuth.isAuthenticated()) {
        console.log('User not authenticated. Showing login screen.');
        document.body.classList.add('auth-hidden');
    } else {
        console.log('Authenticated session found.');
        document.body.classList.remove('auth-hidden');
    }

    // Load settings
    loadSettings();

    // Connect to MT5 server
    try {
        await mt5Connector.connect();
        showSuccess('MT5 sunucusuna bağlanıldı');

        // Listen for account info
        mt5Connector.on('account_info', (accountInfo) => {
            console.log('Hesap bilgisi alındı:', accountInfo);


            // Auto-setup account
            const accountId = `account_${accountInfo.login}`;
            appState.accounts.set(accountId, {
                id: accountId,
                name: accountInfo.name,
                login: accountInfo.login,
                server: accountInfo.server
            });

            // Auto-select this account
            appState.currentAccountId = accountId;

            // Update UI
            setText('chatAccountName', accountInfo.name);

            // Hide account selector since we only have one account
            const accountSelector = document.getElementById('accountSelector');
            if (accountSelector) {
                accountSelector.style.display = 'none';
            }

            // Hide add account button
            const addAccountBtn = document.querySelector('button[onclick="openAddAccountModal()]');
            if (addAccountBtn) {
                addAccountBtn.style.display = 'none';
            }

            // SEND TELEGRAM CONFIG AUTOMATICALLY
            sendTelegramConfig();

            showInfo(`${accountInfo.name} hesabına bağlanıldı`);
        });

    } catch (error) {
        console.error('MT5 sunucusuna bağlanılamadı:', error);
        showError('MT5 sunucusuna bağlanılamadı. Backend\'in çalıştığından emin olun.');
    }

    // Set up event listeners
    setupEventListeners();

    // Set up permanent message handlers (NEW: moved from chat for performance)
    mt5Connector.on('market_analysis', handleMarketAnalysis);
    mt5Connector.on('get_market_analysis_response', handleMarketAnalysis);
    mt5Connector.on('market_analysis_response', handleMarketAnalysis);

    mt5Connector.on('journal_data', (response) => {
        if (window.journal) window.journal.displayJournalData(response);
    });

    mt5Connector.on('note_saved', (response) => {
        if (window.journal) window.journal.onNoteSaved(response.success);
    });

    // Set up real-time updates handler with throttling (NEW: performance fix)
    const throttledUpdate = throttle(handleRealtimeUpdate, 500);
    mt5Connector.on('realtime_update', throttledUpdate);

    console.log('Uygulama hazır!');
});

// ============================================
// EVENT LISTENERS
// ============================================

function setupEventListeners() {
    // Account selector change
    const accountSelector = document.getElementById('accountSelector');
    if (accountSelector) {
        accountSelector.addEventListener('change', (e) => {
            const accountId = e.target.value;
            if (accountId === 'portfolio') {
                switchToPortfolioView();
            } else if (accountId) {
                switchToAccountView(accountId);
            }
        });
    }
}

// ============================================
// ACCOUNT MANAGEMENT
// ============================================
// Note: This app uses auto-connect to the active MT5 account.
// Multi-account management has been removed for simplicity.

async function addAccount(event) {
    // This function is kept for the modal UI but simplified
    // In auto-connect mode, this is not typically used
    event.preventDefault();
    showInfo('Bu uygulama aktif MT5 hesabına otomatik bağlanır. Manuel hesap eklemeye gerek yoktur.');
    closeAddAccountModal();
}

// ============================================
// VIEW SWITCHING
// ============================================

function switchToAccountView(accountId) {
    appState.currentAccountId = accountId;
    appState.currentView = 'dashboard';

    // Show dashboard, hide portfolio
    showElement('dashboardView');
    hideElement('portfolioView');

    // Request account data
    mt5Connector.getAccountData(accountId);

    // Update chat header
    const account = appState.accounts.get(accountId);
    if (account) {
        setText('chatAccountName', account.name);
    }
}

function switchToPortfolioView() {
    appState.currentView = 'portfolio';

    // Hide dashboard, show portfolio
    hideElement('dashboardView');
    showElement('portfolioView');

    // Request portfolio data
    mt5Connector.getPortfolio();
}

// ============================================
// REAL-TIME UPDATES
// ============================================

function handleRealtimeUpdate(data) {
    if (appState.currentView === 'portfolio') {
        // Update portfolio view
        dashboard.updatePortfolioView(data);
    } else if (appState.currentAccountId) {
        // Find current account in data
        const accountData = data.accounts?.find(acc => acc.account_id === appState.currentAccountId);

        if (accountData) {
            updateAccountDashboard(accountData);
        }
    }
}

function updateAccountDashboard(accountData) {
    // Update stats
    dashboard.updateAccountStats(accountData);

    // Update performance metrics
    dashboard.updatePerformanceMetrics(accountData);

    // Update positions
    dashboard.updatePositionsList(accountData.positions || []);

    // Update equity chart
    dashboard.updateEquityChart(accountData.equity);

    // Calculate risk metrics
    const riskMetrics = riskManager.calculateRiskMetrics(accountData);

    // Update risk UI
    riskManager.updateRiskUI(riskMetrics);

    // Check for risk alerts
    checkRiskAlerts(accountData, riskMetrics);

}

function checkRiskAlerts(accountData, riskMetrics) {
    const accountId = accountData.account_id;
    const currentLevel = riskMetrics.riskLevel;
    const previousLevel = appState.lastRiskLevel.get(accountId);

    if (riskManager.shouldAlert(currentLevel, previousLevel)) {
        const message = riskManager.getAlertMessage(currentLevel, riskMetrics);
        if (message) {
            showWarning(message);
        }
    }

    // Update last risk level
    appState.lastRiskLevel.set(accountId, currentLevel);
}

// ============================================
// MODAL HANDLERS
// ============================================

function openAddAccountModal() {
    const modal = document.getElementById('addAccountModal');
    if (modal) {
        modal.classList.add('active');
    }
}

function closeAddAccountModal() {
    const modal = document.getElementById('addAccountModal');
    if (modal) {
        modal.classList.remove('active');
        document.getElementById('addAccountForm').reset();
    }
}

function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        modal.classList.add('active');

        // Load current settings
        document.getElementById('aiProvider').value = aiEngine.provider;
        document.getElementById('aiApiKey').value = aiEngine.apiKey;
        document.getElementById('maxDrawdown').value = riskManager.propFirmRules.maxDrawdown;
        document.getElementById('dailyLimit').value = riskManager.propFirmRules.dailyLimit;
    }
}

function closeSettingsModal() {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

function saveSettings(event) {
    event.preventDefault();

    const provider = document.getElementById('aiProvider').value;
    const apiKey = document.getElementById('aiApiKey').value;
    const maxDrawdown = document.getElementById('maxDrawdown').value;
    const dailyLimit = document.getElementById('dailyLimit').value;

    // Save AI settings
    aiEngine.saveSettings(provider, apiKey);

    // Save risk settings
    riskManager.updateRules(maxDrawdown, dailyLimit);

    // Save Telegram Settings explicitly if on that tab or changed
    saveTelegramSettings();
    sendTelegramConfig(); // Sync with backend immediately

    closeSettingsModal();
    showSuccess('Ayarlar başarıyla kaydedildi!');
}

function loadSettings() {
    // Settings are loaded automatically by aiEngine and riskManager
}

// ============================================
// CHAT INTERFACE
// ============================================

function toggleChat() {
    appState.chatOpen = !appState.chatOpen;
    const chatContainer = document.getElementById('chatContainer');

    if (chatContainer) {
        if (appState.chatOpen) {
            chatContainer.classList.add('active');
        } else {
            chatContainer.classList.remove('active');
        }
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const messagesContainer = document.getElementById('chatMessages');

    if (!input || !messagesContainer) return;

    const message = input.value.trim();
    if (!message) return;

    // Check if account is selected
    if (!appState.currentAccountId) {
        showError('Lütfen önce bir hesap seçin');
        return;
    }

    // Check if API key is configured
    if (!aiEngine.apiKey) {
        showError('Lütfen Ayarlar bölümünden YZ API anahtarını yapılandırın');
        openSettingsModal();
        return;
    }

    // Clear input
    input.value = '';

    // Add user message to chat
    const userMessageEl = document.createElement('div');
    userMessageEl.className = 'chat-message chat-message-user';
    userMessageEl.textContent = message;
    messagesContainer.appendChild(userMessageEl);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Show loading
    const loadingEl = document.createElement('div');
    loadingEl.className = 'chat-message chat-message-ai';
    loadingEl.textContent = '💭 Düşünüyor...';
    messagesContainer.appendChild(loadingEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
        // Get current account data
        const accountData = await getCurrentAccountData();
        const riskMetrics = riskManager.calculateRiskMetrics(accountData);

        // Detect symbol and get market data
        let marketData = null;
        const symbolMatch = message.match(/\b([A-Z]{3,6}|[A-Z]{3}\/[A-Z]{3})\b/i);
        if (symbolMatch) {
            const symbol = symbolMatch[0].toUpperCase();
            try {
                // Wait for the specific response for this request
                loadingEl.textContent = `💭 ${symbol} verileri alınıyor...`;

                // We need to use sendMessage and wait for the specific response type
                const response = await mt5Connector.sendMessage({
                    action: 'get_market_analysis',
                    symbol: symbol
                });

                if (response && response.data && !response.data.error) {
                    marketData = response.data;
                    console.log('Market data received:', marketData);
                }
            } catch (err) {
                console.warn('Could not fetch market data:', err);
            }
        }

        loadingEl.textContent = '💭 Düşünüyor...';

        // Send to AI
        const response = await aiEngine.sendMessage(message, accountData, riskMetrics, marketData);

        // Remove loading
        messagesContainer.removeChild(loadingEl);

        // Check for TRADE_ACTION
        let cleanMessage = response.message;
        const tradeMatch = response.message.match(/\[\[TRADE_ACTION\]\]\s*({.*})/);

        if (tradeMatch) {
            try {
                const tradeData = JSON.parse(tradeMatch[1]);
                console.log('Trade Intent Detected:', tradeData);

                // execute trade
                mt5Connector.send({
                    action: 'execute_complex_trade',
                    symbol: tradeData.symbol.toUpperCase(),
                    trade_action: tradeData.action.toUpperCase(), // BUY or SELL or CLOSE_PARTIAL
                    volume: tradeData.volume,
                    sl_percent: tradeData.sl_percent,
                    rr: tradeData.rr,
                    percent: tradeData.percent // For partial close
                });

                // Show processing indicator
                const processEl = document.createElement('div');
                processEl.className = 'chat-message chat-message-ai';
                processEl.innerHTML = `⚡ <strong>İşlem Başlatılıyor:</strong> ${tradeData.symbol} ${tradeData.action} (Ölçülen Risk: %${tradeData.sl_percent || 'Auto'})<br>Lütfen bekleyin...`;
                messagesContainer.appendChild(processEl);

                // Remove JSON from displayed text
                cleanMessage = response.message.replace(tradeMatch[0], '').trim();

            } catch (e) {
                console.error('Failed to parse trade action:', e);
            }
        }

        // Add AI response
        const aiMessageEl = document.createElement('div');
        aiMessageEl.className = 'chat-message chat-message-ai';
        aiMessageEl.innerHTML = `<strong>${response.emoji} ${response.personality}:</strong><br>${cleanMessage}`;
        messagesContainer.appendChild(aiMessageEl);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

    } catch (error) {
        // Remove loading
        messagesContainer.removeChild(loadingEl);

        // Show error
        const errorEl = document.createElement('div');
        errorEl.className = 'chat-message chat-message-ai';
        errorEl.textContent = `❌ Hata: ${error.message}`;
        messagesContainer.appendChild(errorEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        showError(error.message);
    }
}

function handleMarketAnalysis(data) {
    // Market data received, send to AI if there's a pending message
    if (window.pendingAiMessage) {
        const message = window.pendingAiMessage;
        window.pendingAiMessage = null;

        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages && chatMessages.lastElementChild && chatMessages.lastElementChild.innerHTML.includes('verileri alınıyor')) {
            chatMessages.removeChild(chatMessages.lastElementChild);
        }

        aiEngine.sendMessage(message, appState.accountData, appState.riskMetrics, data);
    }

    // Update Neural Pulse Intelligence
    if (window.neuralPulse && data && data.smc) {
        window.neuralPulse.updateWithRealData(data);
    }
}


async function getCurrentAccountData() {
    // NEW: Use sendMessage for automatic handler cleanup (Performance fix)
    try {
        const response = await mt5Connector.sendMessage({
            action: 'get_account_data',
            account_id: appState.currentAccountId
        });
        return response;
    } catch (err) {
        console.error('Failed to get account data:', err);
        return null;
    }
}

// ============================================
// VIEW SWITCHING
// ============================================

// Make switchView global


function switchView(view) {
    appState.currentView = view;

    // Update tab buttons
    const dashboardTab = document.getElementById('dashboardTab');
    const backtestTab = document.getElementById('backtestTab');

    if (view === 'dashboard') {
        // Show dashboard, hide others
        showElement('dashboardView');
        hideElement('backtestView');
        hideElement('journalView');
        hideElement('neuralView');
        if (document.getElementById('strategies-view')) document.getElementById('strategies-view').style.display = 'none';

        // Update button styles
        if (dashboardTab) {
            dashboardTab.className = 'btn btn-primary';
        }
        if (backtestTab) {
            backtestTab.className = 'btn btn-outline';
        }
    } else if (view === 'backtest') {
        // Hide others, show backtest
        hideElement('dashboardView');
        showElement('backtestView');
        hideElement('journalView');
        hideElement('neuralView');
        if (document.getElementById('strategies-view')) document.getElementById('strategies-view').style.display = 'none';

        // Update button styles
        if (dashboardTab) dashboardTab.className = 'btn btn-outline';
        if (backtestTab) backtestTab.className = 'btn btn-primary';
        const journalTab = document.getElementById('journalTab');
        if (journalTab) journalTab.className = 'btn btn-outline';

    } else if (view === 'journal') {
        // Hide others, show journal
        hideElement('dashboardView');
        hideElement('backtestView');
        showElement('journalView');
        hideElement('neuralView');
        if (document.getElementById('strategies-view')) document.getElementById('strategies-view').style.display = 'none';

        // Update button styles
        if (dashboardTab) dashboardTab.className = 'btn btn-outline';
        if (backtestTab) backtestTab.className = 'btn btn-outline';
        const journalTab = document.getElementById('journalTab');
        if (journalTab) journalTab.className = 'btn btn-primary';

    } else if (view === 'strategies') {
        // Hide others, show strategies
        hideElement('dashboardView');
        hideElement('backtestView');
        hideElement('journalView');
        hideElement('neuralView');
        if (document.getElementById('strategies-view')) document.getElementById('strategies-view').style.display = 'block';

        // Update button styles
        if (dashboardTab) dashboardTab.className = 'btn btn-outline';
        if (backtestTab) backtestTab.className = 'btn btn-outline';
        const journalTab = document.getElementById('journalTab');
        if (journalTab) journalTab.className = 'btn btn-outline';
    } else if (view === 'neural') {
        // Hide others, show neural
        hideElement('dashboardView');
        hideElement('backtestView');
        hideElement('journalView');
        showElement('neuralView');
        if (document.getElementById('strategies-view')) document.getElementById('strategies-view').style.display = 'none';

        // Update button styles
        if (dashboardTab) dashboardTab.className = 'btn btn-outline';
        if (backtestTab) backtestTab.className = 'btn btn-outline';
        const journalTab = document.getElementById('journalTab');
        if (journalTab) journalTab.className = 'btn btn-outline';
        const neuralTab = document.getElementById('neuralTab');
        if (neuralTab) neuralTab.className = 'btn btn-primary';

        // Initialize Neural Pulse
        if (window.neuralPulse) {
            window.neuralPulse.init();
        }
    }

}

// ============================================
// CLOSE MODALS ON OUTSIDE CLICK
// ============================================

document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
    }
});

// ============================================
// EXPORTS FOR HTML INLINE HANDLERS
// ============================================

window.openAddAccountModal = openAddAccountModal;
window.closeAddAccountModal = closeAddAccountModal;
window.openSettingsModal = openSettingsModal;
window.closeSettingsModal = closeSettingsModal;
window.toggleChat = toggleChat;
window.addAccount = addAccount;
window.saveSettings = saveSettings;
window.sendChatMessage = sendChatMessage;
window.handleChatKeyPress = handleChatKeyPress;
window.switchView = switchView;

// ============================================
// SAAS AUTH UI HANDLERS
// ============================================

window.switchAuthTab = function (tab) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const tabs = document.querySelectorAll('.auth-tab');

    if (tab === 'login') {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        tabs[0].classList.add('active');
        tabs[1].classList.remove('active');
    } else {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        tabs[0].classList.remove('active');
        tabs[1].classList.add('active');
    }
}

window.handleAuthAction = async function (event, type) {
    event.preventDefault();
    const btn = event.submitter;
    const originalText = btn.textContent;
    btn.textContent = 'İşleniyor...';
    btn.disabled = true;

    try {
        if (type === 'login') {
            const email = document.getElementById('loginEmail').value;
            const pass = document.getElementById('loginPassword').value;
            const result = await uceAuth.login(email, pass);

            if (result.success) {
                showSuccess('Giriş başarılı! UceAsistan\'a hoş geldiniz.');
                document.body.classList.remove('auth-hidden');
            } else {
                showError(result.error);
            }
        } else {
            const email = document.getElementById('regEmail').value;
            const pass = document.getElementById('regPassword').value;
            const result = await uceAuth.register(email, pass);

            if (result.success) {
                showInfo(result.message);
                switchAuthTab('login');
            }
        }
    } catch (err) {
        showError('Bir hata oluştu: ' + err.message);
    } finally {
        if (btn) {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }
}

// ============================================
// SAAS SETTINGS HANDLERS
// ============================================

window.switchSettingsTab = function (tab) {
    const general = document.getElementById('generalSettings');
    const telegram = document.getElementById('telegramSettings');
    const videos = document.getElementById('videosSettings');
    const account = document.getElementById('accountSettings');
    const actions = document.getElementById('settingsActionButtons');
    const tabs = document.querySelectorAll('#settingsModal .auth-tab');

    // Hide all sections first
    general.classList.add('hidden');
    if (telegram) telegram.classList.add('hidden');
    if (videos) videos.classList.add('hidden');
    account.classList.add('hidden');

    // Remove active from all tabs
    tabs.forEach(t => t.classList.remove('active'));

    if (tab === 'general') {
        general.classList.remove('hidden');
        actions.classList.remove('hidden');
        tabs[0].classList.add('active');
    } else if (tab === 'telegram') {
        if (telegram) telegram.classList.remove('hidden');
        actions.classList.remove('hidden');
        tabs[1].classList.add('active');

        // Load saved Telegram settings
        loadTelegramSettings();
    } else if (tab === 'videos') {
        if (videos) videos.classList.remove('hidden');
        actions.classList.add('hidden'); // Hide save button for videos tab
        tabs[2].classList.add('active');
    } else if (tab === 'account') {
        account.classList.remove('hidden');
        actions.classList.add('hidden');
        tabs[3].classList.add('active');

        // Populate account info
        const sub = uceAuth.getSubscriptionDetails();
        if (sub) {
            setText('subEmail', uceAuth.user.email);
            setText('subPlanBadge', sub.plan + ' Plan');
            setText('subExpiry', formatDateTime(sub.expiry));
        }
    }
}

// ============================================
// TELEGRAM INTEGRATION
// ============================================

function loadTelegramSettings() {
    const saved = localStorage.getItem('uce_telegram_settings');
    if (saved) {
        try {
            const settings = JSON.parse(saved);
            document.getElementById('telegramBotToken').value = settings.botToken || '';
            document.getElementById('telegramChatId').value = settings.chatId || '';
            document.getElementById('telegramRiskAlerts').checked = settings.riskAlerts !== false;
            document.getElementById('telegramConfluence').checked = settings.confluence !== false;
            document.getElementById('telegramTrades').checked = settings.trades !== false;
        } catch (e) {
            console.warn('Failed to load Telegram settings:', e);
        }
    }
}

function saveTelegramSettings() {
    const settings = {
        botToken: document.getElementById('telegramBotToken').value,
        chatId: document.getElementById('telegramChatId').value,
        riskAlerts: document.getElementById('telegramRiskAlerts').checked,
        confluence: document.getElementById('telegramConfluence').checked,
        trades: document.getElementById('telegramTrades').checked
    };
    localStorage.setItem('uce_telegram_settings', JSON.stringify(settings));
}

// NEW: Send config to backend automatically
window.sendTelegramConfig = function () {
    const saved = localStorage.getItem('uce_telegram_settings');
    if (saved) {
        try {
            const settings = JSON.parse(saved);
            if (settings.botToken && settings.chatId) {
                console.log('Sending Telegram config to backend...');

                // Get risk settings as well
                const maxDrawdown = document.getElementById('maxDrawdown').value || 10.0;
                const dailyLimit = document.getElementById('dailyLimit').value || 500.0;

                mt5Connector.send({
                    action: 'configure_telegram',
                    bot_token: settings.botToken,
                    chat_id: settings.chatId,
                    max_drawdown: parseFloat(maxDrawdown),
                    daily_limit: parseFloat(dailyLimit)
                });
            }
        } catch (e) {
            console.error('Error sending Telegram config:', e);
        }
    }
}

window.testTelegramConnection = async function () {
    const botToken = document.getElementById('telegramBotToken').value;
    const chatId = document.getElementById('telegramChatId').value;
    const maxDrawdown = document.getElementById('maxDrawdown').value;
    const dailyLimit = document.getElementById('dailyLimit').value;
    const statusEl = document.getElementById('telegramStatus');

    if (!botToken || !chatId) {
        showError('Bot Token ve Chat ID gereklidir');
        return;
    }

    statusEl.innerHTML = '<div class="badge badge-outline">🔄 Bağlantı test ediliyor...</div>';
    statusEl.style.display = 'block';

    try {
        // Send configuration to backend
        mt5Connector.on('telegram_configured', (response) => {
            if (response.success) {
                statusEl.innerHTML = `
                    <div class="badge badge-success">✅ Bağlantı Başarılı</div>
                    <p class="text-sm text-secondary mt-sm">Bot: ${response.bot_name}</p>
                `;
                saveTelegramSettings();
                showSuccess('Telegram botu yapılandırıldı!');
            } else {
                statusEl.innerHTML = `
                    <div class="badge badge-danger">❌ Bağlantı Başarısız</div>
                    <p class="text-sm text-secondary mt-sm">${response.error}</p>
                `;
                showError('Telegram bağlantısı başarısız: ' + response.error);
            }
        });

        mt5Connector.send({
            action: 'configure_telegram',
            bot_token: botToken,
            chat_id: chatId,
            max_drawdown: parseFloat(maxDrawdown) || 10.0,
            daily_limit: parseFloat(dailyLimit) || 500.0
        });

    } catch (error) {
        statusEl.innerHTML = `
            <div class="badge badge-danger">❌ Hata</div>
            <p class="text-sm text-secondary mt-sm">${error.message}</p>
        `;
        showError('Telegram yapılandırma hatası: ' + error.message);
    }
}

window.sendTestTelegramMessage = async function () {
    const statusEl = document.getElementById('telegramStatus');

    statusEl.innerHTML = '<div class="badge badge-outline">📤 Test mesajı gönderiliyor...</div>';
    statusEl.style.display = 'block';

    try {
        mt5Connector.on('telegram_test_result', (response) => {
            if (response.success) {
                statusEl.innerHTML = `
                    <div class="badge badge-success">✅ Test Mesajı Gönderildi</div>
                    <p class="text-sm text-secondary mt-sm">Telegram'ınızı kontrol edin!</p>
                `;
                showSuccess('Test mesajı Telegram\'a gönderildi!');
            } else {
                statusEl.innerHTML = `
                    <div class="badge badge-danger">❌ Gönderilemedi</div>
                `;
                showError('Test mesajı gönderilemedi. Önce bağlantıyı test edin.');
            }
        });

        mt5Connector.send({
            action: 'test_telegram'
        });

    } catch (error) {
        showError('Test mesajı hatası: ' + error.message);
    }
}

// ============================================
// DASHBOARD STRATEGY LAUNCHER
// ============================================

window.loadDashboardStrategies = async function () {
    const select = document.getElementById('dashboardStrategySelect');
    if (!select) return;

    let options = '<option value="">-- Strateji Seç --</option>';

    try {
        // User templates
        const response = await mt5Connector.sendMessage({ action: 'get_user_templates' });
        // Handle both array and {data: []} formats
        const userTemplates = Array.isArray(response) ? response : (response && response.data ? response.data : []);
        if (userTemplates.length > 0) {
            options += '<optgroup label="👤 Benim Şablonlarım">';
            options += userTemplates.map(t =>
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

    // Also load MT5 symbols
    try {
        const symResponse = await mt5Connector.sendMessage({ action: 'get_mt5_symbols' });
        const symSelect = document.getElementById('dashboardSymbolSelect');
        if (symResponse && symResponse.data && symSelect) {
            symSelect.innerHTML = symResponse.data.map(sym =>
                `<option value="${sym}">${sym}</option>`
            ).join('');
        }
    } catch (e) { }
};

window.quickLaunchFromDashboard = async function () {
    const strategyValue = document.getElementById('dashboardStrategySelect')?.value;
    const symbol = document.getElementById('dashboardSymbolSelect')?.value || 'EURUSD';
    const timeframe = document.getElementById('dashboardTimeframe')?.value || 'H1';

    if (!strategyValue) {
        showError('Lütfen bir strateji seçin');
        return;
    }

    let strategyCode = '';

    // Get strategy code
    if (strategyValue.startsWith('user:')) {
        const templateId = strategyValue.replace('user:', '');
        const response = await mt5Connector.sendMessage({ action: 'get_user_templates' });
        // Handle both array and {data: []} formats
        const templates = Array.isArray(response) ? response : (response && response.data ? response.data : []);
        const template = templates.find(t => t.id === templateId);
        if (template) {
            strategyCode = template.code;
        }
    } else if (strategyValue.startsWith('builtin:')) {
        const templateId = strategyValue.replace('builtin:', '');
        const response = await mt5Connector.sendMessage({
            action: 'load_template',
            template_id: templateId
        });
        if (response?.data?.success) {
            strategyCode = response.data.code;
        }
    }

    if (!strategyCode) {
        showError('Strateji kodu yüklenemedi');
        return;
    }

    // Start live trading
    showSuccess('🚀 Canlı işlem başlatılıyor...');

    const result = await mt5Connector.sendMessage({
        action: 'start_live_trading',
        strategy_code: strategyCode,
        symbol: symbol,
        timeframe: timeframe,
        lot_size: 0.01,
        rr_ratio: 2.0
    });

    if (result && result.success) {
        showSuccess(`✅ ${symbol} ${timeframe} üzerinde canlı işlem başlatıldı!`);

        // Update status indicator
        const statusDiv = document.getElementById('liveTraderStatus');
        const infoSpan = document.getElementById('liveTraderInfo');
        if (statusDiv && infoSpan) {
            statusDiv.style.display = 'block';
            infoSpan.textContent = `${symbol} ${timeframe}`;
        }
    } else {
        showError('Canlı işlem başlatılamadı: ' + (result?.message || 'Bilinmeyen hata'));
    }
};

// Load dashboard strategies on page load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        if (typeof loadDashboardStrategies === 'function') {
            loadDashboardStrategies();
        }
    }, 2000);
});
