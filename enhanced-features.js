/**
 * Enhanced Features - Conversation Wizard & Optimizer
 */

// ============================================
// CONVERSATION WIZARD
// ============================================

let wizardState = {
    sessionId: null,
    currentStep: 0,
    totalSteps: 3,
    answers: {},
    questions: []
};

// Hardcoded questions (offline mode)
const wizardQuestions = [
    {
        id: 'timeframe',
        question: 'Hangi zaman diliminde çalışmasını istersin?',
        options: [
            { value: 'M5', label: 'M5 (5 Dakika) - Scalping' },
            { value: 'M15', label: 'M15 (15 Dakika) - Kısa Vade' },
            { value: 'H1', label: 'H1 (1 Saat) - Orta Vade' },
            { value: 'H4', label: 'H4 (4 Saat) - Swing' },
            { value: 'D1', label: 'D1 (Günlük) - Uzun Vade' }
        ]
    },
    {
        id: 'risk_level',
        question: 'Risk seviyesi nasıl olsun?',
        options: [
            { value: 'low', label: 'Düşük - Muhafazakar (Win rate > %60)' },
            { value: 'medium', label: 'Orta - Dengeli (Win rate ~%50)' },
            { value: 'high', label: 'Yüksek - Agresif (Büyük R:R)' }
        ]
    },
    {
        id: 'stop_loss_profile',
        question: 'Stop Loss profili nasıl olsun? (ATR bazlı)',
        options: [
            { value: 'hard', label: '🔴 Hard Stop - Sıkı (0.5x ATR) - Hızlı kes' },
            { value: 'mid', label: '🟡 Mid Stop - Dengeli (1x ATR) - Standart' },
            { value: 'low', label: '🟢 Low Stop - Geniş (2x ATR) - Nefes ver' }
        ]
    },
    {
        id: 'trading_style',
        question: 'Hangi tarz trading yapmak istersin?',
        options: [
            { value: 'trend', label: 'Trend Takibi - Trendle git' },
            { value: 'reversal', label: 'Reversal - Dönüş noktalarını yakala' },
            { value: 'breakout', label: 'Breakout - Kırılımları yakala' },
            { value: 'range', label: 'Range Trading - Yatay piyasada al-sat' }
        ]
    }
];

function openConversationWizard() {
    const description = document.getElementById('strategyDescription').value;

    if (!description.trim()) {
        showError('Lütfen önce bir strateji açıklaması girin');
        return;
    }

    // Reset state
    wizardState.sessionId = 'wizard_' + Date.now();
    wizardState.currentStep = 0;
    wizardState.answers = {};
    wizardState.originalDescription = description;

    // Show modal
    const modal = document.getElementById('conversationWizardModal');
    modal.style.display = 'flex';
    setTimeout(() => modal.classList.add('active'), 10);

    // Show first question
    displayWizardQuestion(wizardQuestions[0]);
}

function closeConversationWizard() {
    const modal = document.getElementById('conversationWizardModal');
    modal.classList.remove('active');
    setTimeout(() => modal.style.display = 'none', 300);
}

function displayWizardQuestion(question) {
    document.getElementById('wizardQuestion').textContent = question.question;

    const optionsContainer = document.getElementById('wizardOptions');
    optionsContainer.innerHTML = '';

    // Create option buttons
    question.options.forEach(option => {
        const btn = document.createElement('button');
        btn.className = 'btn btn-outline';
        btn.textContent = option.label;
        btn.style.textAlign = 'left';
        btn.style.justifyContent = 'flex-start';
        btn.onclick = () => selectWizardOption(question.id, option.value, btn);
        optionsContainer.appendChild(btn);
    });

    // Update progress
    updateWizardProgress();

    // Disable next button until selection
    document.getElementById('wizardNextBtn').disabled = true;
}

function updateWizardProgress() {
    const totalSteps = wizardQuestions.length; // Should be 4
    const currentStep = wizardState.currentStep + 1;
    const progress = Math.round((currentStep / totalSteps) * 100);

    // Update step counter
    const stepElement = document.getElementById('wizardCurrentStep');
    if (stepElement) {
        stepElement.textContent = currentStep;
    }

    // Update progress bar
    const progressElement = document.getElementById('wizardProgress');
    if (progressElement) {
        progressElement.textContent = progress;
    }

    const progressBar = document.querySelector('.wizard-progress-bar');
    if (progressBar) {
        progressBar.style.width = progress + '%';
    }
}

function selectWizardOption(questionId, value, button) {
    // Store answer
    wizardState.answers[questionId] = value;

    // Visual feedback
    const allButtons = document.getElementById('wizardOptions').querySelectorAll('.btn');
    allButtons.forEach(btn => btn.classList.remove('btn-primary'));
    allButtons.forEach(btn => btn.classList.add('btn-outline'));
    button.classList.remove('btn-outline');
    button.classList.add('btn-primary');

    // Enable next button
    document.getElementById('wizardNextBtn').disabled = false;
}

function wizardNextStep() {
    wizardState.currentStep++;

    if (wizardState.currentStep < wizardQuestions.length) {
        // Show next question
        displayWizardQuestion(wizardQuestions[wizardState.currentStep]);
        document.getElementById('wizardBackBtn').disabled = false;
    } else {
        // All questions answered
        showWizardFinish();
    }
}

function wizardPreviousStep() {
    if (wizardState.currentStep > 0) {
        wizardState.currentStep--;
        displayWizardQuestion(wizardQuestions[wizardState.currentStep]);
        updateWizardProgress();

        // Re-select previous answer if exists
        const currentQuestion = wizardQuestions[wizardState.currentStep];
        const previousAnswer = wizardState.answers[currentQuestion.id];
        if (previousAnswer) {
            document.getElementById('wizardNextBtn').disabled = false;
        }
    }
}

function showWizardFinish() {
    document.getElementById('wizardNextBtn').style.display = 'none';
    document.getElementById('wizardFinishBtn').style.display = 'block';
    document.getElementById('wizardQuestion').textContent = '✅ Tüm sorular cevaplandı!';
    document.getElementById('wizardOptions').innerHTML = '<p class="text-secondary">Strateji oluşturmak için "Strateji Oluştur" butonuna tıklayın.</p>';
}

function wizardFinish() {
    // Generate enhanced prompt
    const original = wizardState.originalDescription;
    const answers = wizardState.answers;

    const riskMap = {
        low: 'Conservative (high win rate, tight stops)',
        medium: 'Balanced (moderate risk-reward)',
        high: 'Aggressive (high risk-reward ratio)'
    };

    const styleMap = {
        trend: 'Trend following - use moving averages and trend indicators',
        reversal: 'Reversal trading - look for overbought/oversold conditions',
        breakout: 'Breakout trading - detect range breakouts',
        range: 'Range trading - buy support, sell resistance'
    };

    const stopLossMap = {
        hard: '0.5x ATR (tight stop, quick exit)',
        mid: '1x ATR (standard stop)',
        low: '2x ATR (wide stop, room to breathe)'
    };

    // Get stop loss multiplier
    const slMultiplier = answers.stop_loss_profile === 'hard' ? '0.5' :
        answers.stop_loss_profile === 'mid' ? '1' : '2';

    const enhancedPrompt = `${original}

**User Preferences:**
- Timeframe: ${answers.timeframe}
- Risk Level: ${riskMap[answers.risk_level] || answers.risk_level}
- Stop Loss Profile: ${stopLossMap[answers.stop_loss_profile] || 'Standard (1x ATR)'}
- Trading Style: ${styleMap[answers.trading_style] || answers.trading_style}

**CRITICAL - ATR-Based Stop Loss Implementation:**
You MUST implement ATR-based stop loss with these exact specifications:
1. Calculate ATR(14): atr = (data['high'] - data['low']).rolling(14).mean()
2. Stop Loss Distance: ${slMultiplier} * ATR
3. In your strategy function, add these lines:
   - atr = (data['high'] - data['low']).rolling(14).mean()
   - stop_distance = ${slMultiplier} * atr.iloc[-1]
   - For LONG: stop_loss = entry_price - stop_distance
   - For SHORT: stop_loss = entry_price + stop_distance

Generate a complete strategy with ATR-based stop loss included in the code.`;

    // Close wizard
    closeConversationWizard();

    // Fill description
    document.getElementById('strategyDescription').value = enhancedPrompt;

    // Auto-generate
    showSuccess('✨ Gelişmiş prompt oluşturuldu! ATR bazlı stop loss eklenecek.');
    setTimeout(() => generateStrategy(), 500);
}

function updateWizardProgress() {
    const progress = ((wizardState.currentStep + 1) / wizardQuestions.length) * 100;
    document.getElementById('wizardCurrentStep').textContent = wizardState.currentStep + 1;
    document.getElementById('wizardProgress').textContent = Math.round(progress);
    document.getElementById('wizardProgressBar').style.width = progress + '%';
}

function closeConversationWizard() {
    const modal = document.getElementById('conversationWizardModal');
    modal.classList.remove('active');
    setTimeout(() => modal.style.display = 'none', 300);

    wizardState = {
        sessionId: null,
        currentStep: 0,
        totalSteps: 3,
        answers: {},
        questions: [],
        originalDescription: ''
    };
}

// ============================================
// OPTIMIZER
// ============================================

let optimizerState = {
    suggestions: [],
    backtestResults: null
};

function showOptimizerResults(backtestResults) {
    optimizerState.backtestResults = backtestResults;

    // Show modal - use CSS active class
    const modal = document.getElementById('optimizerModal');
    modal.style.display = 'flex';
    setTimeout(() => modal.classList.add('active'), 10);

    // Display backtest summary
    const metrics = backtestResults.metrics;
    document.getElementById('optWinRate').textContent = metrics.win_rate.toFixed(1) + '%';
    document.getElementById('optProfitFactor').textContent = metrics.profit_factor.toFixed(2);
    document.getElementById('optDrawdown').textContent = metrics.max_drawdown_pct.toFixed(1) + '%';
    document.getElementById('optTrades').textContent = metrics.total_trades;

    // Get optimization suggestions from backend
    getOptimizationSuggestions(backtestResults);
}

async function getOptimizationSuggestions(backtestResults) {
    try {
        const strategyCode = document.getElementById('strategyCode').value;

        const response = await mt5Connector.sendMessage({
            action: 'optimize_strategy',
            strategy_code: strategyCode,
            backtest_results: backtestResults
        });

        if (response && response.suggestions) {
            optimizerState.suggestions = response.suggestions;
            displayOptimizationSuggestions(response.suggestions);
        }
    } catch (error) {
        console.error('Optimizer error:', error);
        showError('Optimizasyon önerileri alınamadı: ' + error.message);
    }
}

function displayOptimizationSuggestions(suggestions) {
    const container = document.getElementById('optimizerSuggestions');
    container.innerHTML = '';

    if (suggestions.length === 0) {
        container.innerHTML = '<p class="text-secondary">Öneri bulunamadı.</p>';
        return;
    }

    // Group by priority
    const critical = suggestions.filter(s => s.priority === 'critical');
    const high = suggestions.filter(s => s.priority === 'high');
    const medium = suggestions.filter(s => s.priority === 'medium');
    const low = suggestions.filter(s => s.priority === 'low');

    // Display critical
    if (critical.length > 0) {
        container.innerHTML += '<h3 class="mb-md" style="color: #f45c43;">🚨 KRİTİK SORUNLAR</h3>';
        critical.forEach(s => container.appendChild(createSuggestionCard(s)));
    }

    // Display high
    if (high.length > 0) {
        container.innerHTML += '<h3 class="mb-md mt-lg" style="color: #f5a623;">⚠️ YÜKSEK ÖNCELİK</h3>';
        high.forEach(s => container.appendChild(createSuggestionCard(s)));
    }

    // Display medium
    if (medium.length > 0) {
        container.innerHTML += '<h3 class="mb-md mt-lg" style="color: #4a90e2;">📌 ORTA ÖNCELİK</h3>';
        medium.forEach(s => container.appendChild(createSuggestionCard(s)));
    }

    // Display low
    if (low.length > 0) {
        container.innerHTML += '<h3 class="mb-md mt-lg" style="color: #7ed321;">💡 ÖNERİLER</h3>';
        low.forEach(s => container.appendChild(createSuggestionCard(s)));
    }
}

function createSuggestionCard(suggestion) {
    const card = document.createElement('div');
    card.className = 'mb-md p-md';
    card.style.background = 'rgba(255,255,255,0.05)';
    card.style.borderRadius = 'var(--radius-md)';
    card.style.border = '1px solid rgba(255,255,255,0.1)';

    const priorityColors = {
        critical: '#f45c43',
        high: '#f5a623',
        medium: '#4a90e2',
        low: '#7ed321'
    };

    card.innerHTML = `
        <div class="flex justify-between items-center mb-sm">
            <strong style="color: ${priorityColors[suggestion.priority]};">${suggestion.issue}</strong>
            <button class="btn btn-sm btn-primary" onclick="applySuggestion(${optimizerState.suggestions.indexOf(suggestion)})">
                Uygula
            </button>
        </div>
        <p class="text-secondary mb-sm">${suggestion.suggestion}</p>
        ${suggestion.code_change ? `
            <details class="mt-sm">
                <summary class="text-sm text-secondary" style="cursor: pointer;">Kod değişikliğini gör</summary>
                <pre class="mt-sm p-sm" style="background: rgba(0,0,0,0.3); border-radius: 4px; overflow-x: auto; font-size: 12px;">${suggestion.code_change}</pre>
            </details>
        ` : ''}
    `;

    return card;
}

function applySuggestion(index) {
    const suggestion = optimizerState.suggestions[index];

    if (!suggestion.code_change) {
        showInfo('Bu öneri için otomatik kod değişikliği yok');
        return;
    }

    // Get current code from the CORRECT textarea
    const codeTextarea = document.getElementById('strategyCode');
    if (!codeTextarea) {
        showError('Strateji kod alanı bulunamadı!');
        return;
    }

    const currentCode = codeTextarea.value;
    const newCode = currentCode + '\n\n# ÖNERİ UYGULANMIŞ:\n' + suggestion.code_change;

    codeTextarea.value = newCode;

    // Visual feedback
    showSuccess('✅ Öneri uygulandı! Kodu kontrol edin.');

    // Scroll to code section
    setTimeout(() => {
        codeTextarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 300);
}

function applyAllOptimizations() {
    const suggestions = optimizerState.suggestions.filter(s => s.code_change);

    if (suggestions.length === 0) {
        showInfo('Uygulanabilir öneri yok');
        return;
    }

    let currentCode = document.getElementById('strategyCode').value;

    suggestions.forEach(s => {
        currentCode += '\n\n' + s.code_change;
    });

    document.getElementById('strategyCode').value = currentCode;
    showSuccess(`✅ ${suggestions.length} öneri uygulandı!`);
    closeOptimizerModal();
}

function closeOptimizerModal() {
    const modal = document.getElementById('optimizerModal');
    modal.classList.remove('active');
    setTimeout(() => modal.style.display = 'none', 300);
}

// ============================================
// TEMPLATE GALLERY
// ============================================

// Template data (matching backend strategy_templates.py)
const templateGalleryData = {
    'rsi_oversold': {
        id: 'rsi_oversold',
        name: 'RSI Aşırı Satım/Alım',
        category: 'Oscillator',
        icon: '📊',
        description: 'RSI 30\'un altında al, 70\'in üstünde sat',
        timeframe: 'H1',
        difficulty: 'Kolay',
        winRate: '~55%'
    },
    'sma_crossover': {
        id: 'sma_crossover',
        name: 'SMA Kesişimi (Golden/Death Cross)',
        category: 'Trend Following',
        icon: '📈',
        description: 'SMA 50, SMA 200\'ü yukarı keserse al (Golden Cross)',
        timeframe: 'D1',
        difficulty: 'Kolay',
        winRate: '~50%'
    },
    'ict_fvg': {
        id: 'ict_fvg',
        name: 'ICT Fair Value Gap',
        category: 'ICT/Smart Money',
        icon: '🎯',
        description: 'Fair Value Gap (boşluk) oluştuğunda trade al',
        timeframe: 'H1',
        difficulty: 'Orta',
        winRate: '~60%'
    },
    'breakout': {
        id: 'breakout',
        name: 'Breakout (Kırılım)',
        category: 'Breakout',
        icon: '💥',
        description: 'Son 20 barın en yüksek/düşük seviyesini kırdığında trade',
        timeframe: 'H4',
        difficulty: 'Orta',
        winRate: '~45%'
    },
    'mean_reversion': {
        id: 'mean_reversion',
        name: 'Mean Reversion (Bollinger)',
        category: 'Mean Reversion',
        icon: '🔄',
        description: 'Fiyat alt banda değerse al, üst banda değerse sat',
        timeframe: 'H1',
        difficulty: 'Kolay',
        winRate: '~52%'
    },
    'ict_smart_money': {
        id: 'ict_smart_money',
        name: 'ICT Smart Money (Tested)',
        category: 'ICT/Smart Money',
        icon: '💎',
        description: 'Trend + Discount/Premium + FVG/OB (137 trade, %15 getiri)',
        timeframe: 'H1',
        difficulty: 'Orta',
        winRate: '~44%'
    }
};

async function showTemplateGallery() {
    // Create modal if it doesn't exist
    let modal = document.getElementById('templateGalleryModal');

    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'templateGalleryModal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal glass-card" style="max-width: 900px; max-height: 80vh; overflow-y: auto;">
                <div class="modal-header flex justify-between items-center mb-lg">
                    <h2>📚 Strateji Şablon Galerisi</h2>
                    <button class="btn btn-ghost" onclick="closeTemplateGallery()">✕</button>
                </div>
                <p class="text-secondary mb-lg">Hazır stratejilerden birini seçin veya kendi stratejinizi yazın.</p>
                <div id="templateGalleryGrid" class="template-gallery-grid"></div>
            </div>
        `;
        document.body.appendChild(modal);

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .template-gallery-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                gap: var(--space-md);
            }
            .template-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: var(--radius-lg);
                padding: var(--space-md);
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .template-card:hover {
                background: rgba(255, 255, 255, 0.1);
                border-color: var(--primary);
                transform: translateY(-2px);
            }
            .template-card-header {
                display: flex;
                align-items: center;
                gap: var(--space-sm);
                margin-bottom: var(--space-sm);
            }
            .template-icon {
                font-size: 2rem;
            }
            .template-category {
                font-size: 0.75rem;
                padding: 2px 8px;
                background: rgba(102, 126, 234, 0.2);
                border-radius: 12px;
                color: var(--primary);
            }
            .template-meta {
                display: flex;
                gap: var(--space-md);
                font-size: 0.8rem;
                color: var(--text-secondary);
            }
            .template-card-user {
                border-color: var(--success);
                position: relative;
            }
            .template-delete-btn {
                position: absolute;
                top: 8px;
                right: 8px;
                background: rgba(239, 68, 68, 0.8);
                border: none;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                cursor: pointer;
                color: white;
                font-size: 12px;
                opacity: 0;
                transition: opacity 0.2s;
            }
            .template-card:hover .template-delete-btn {
                opacity: 1;
            }
            .template-section-title {
                grid-column: 1 / -1;
                font-size: 1.1rem;
                font-weight: 600;
                margin-top: var(--space-md);
                padding-bottom: var(--space-sm);
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
        `;
        document.head.appendChild(style);
    }

    // Render template cards - first built-in, then user templates
    const grid = document.getElementById('templateGalleryGrid');

    // Built-in templates
    let html = '<div class="template-section-title">📦 Hazır Şablonlar</div>';
    html += Object.values(templateGalleryData).map(template => `
        <div class="template-card" onclick="selectTemplateFromGallery('${template.id}')">
            <div class="template-card-header">
                <span class="template-icon">${template.icon}</span>
                <div>
                    <div style="font-weight: 600;">${template.name}</div>
                    <span class="template-category">${template.category}</span>
                </div>
            </div>
            <p class="text-secondary text-sm mb-sm">${template.description}</p>
            <div class="template-meta">
                <span>⏱️ ${template.timeframe}</span>
                <span>📊 ${template.winRate}</span>
                <span>🎯 ${template.difficulty}</span>
            </div>
        </div>
    `).join('');

    grid.innerHTML = html;

    // Show modal FIRST (before async fetch)
    modal.style.display = 'flex';
    setTimeout(() => modal.classList.add('active'), 10);

    // Fetch user templates from backend (async, after modal is shown)
    try {
        const response = await mt5Connector.sendMessage({ action: 'get_user_templates' });
        // Handle both array and {data: []} formats
        const userTemplates = Array.isArray(response) ? response : (response && response.data ? response.data : []);
        if (userTemplates.length > 0) {
            let userHtml = '<div class="template-section-title">👤 Benim Şablonlarım</div>';
            userHtml += userTemplates.map(template => `
                <div class="template-card template-card-user" onclick="selectUserTemplate('${template.id}')">
                    <button class="template-delete-btn" onclick="event.stopPropagation(); deleteUserTemplate('${template.id}', '${template.name}')">🗑️</button>
                    <div class="template-card-header">
                        <span class="template-icon">⭐</span>
                        <div>
                            <div style="font-weight: 600;">${template.name}</div>
                            <span class="template-category">Kullanıcı</span>
                        </div>
                    </div>
                    <p class="text-secondary text-sm mb-sm">${template.description || 'Özel strateji'}</p>
                    <div class="template-meta">
                        <span>⏱️ ${template.timeframe || 'H1'}</span>
                        <span>📅 ${new Date(template.created_at).toLocaleDateString('tr-TR')}</span>
                    </div>
                </div>
            `).join('');
            grid.innerHTML += userHtml;
        }
    } catch (e) {
        console.log('Could not fetch user templates:', e);
    }
}

function closeTemplateGallery() {
    const modal = document.getElementById('templateGalleryModal');
    if (modal) {
        modal.classList.remove('active');
        setTimeout(() => modal.style.display = 'none', 300);
    }
}

async function selectTemplateFromGallery(templateId) {
    closeTemplateGallery();

    // Set dropdown value
    const selector = document.getElementById('templateSelector');
    if (selector) {
        selector.value = templateId;
    }

    // Load the template using existing function
    if (typeof loadTemplate === 'function') {
        await loadTemplate();
    } else if (window.backtest && typeof window.backtest.loadTemplate === 'function') {
        await window.backtest.loadTemplate();
    }
}

// Select and load user template
async function selectUserTemplate(templateId) {
    closeTemplateGallery();

    try {
        const response = await mt5Connector.sendMessage({ action: 'get_user_templates' });
        // Handle both array and {data: []} formats
        const templates = Array.isArray(response) ? response : (response && response.data ? response.data : []);
        const template = templates.find(t => t.id === templateId);
        if (template) {
            // Load code into editor
            document.getElementById('strategyCode').value = template.code;
            document.getElementById('strategyDescription').value = template.description || '';

            // Show code section
            document.getElementById('generatedCodeSection').style.display = 'block';

            showSuccess(`"${template.name}" şablonu yüklendi!`);
        }
    } catch (e) {
        showError('Şablon yüklenemedi: ' + e.message);
    }
}

// Delete user template
async function deleteUserTemplate(templateId, templateName) {
    if (!confirm(`"${templateName}" şablonunu silmek istediğinize emin misiniz?`)) {
        return;
    }

    try {
        const response = await mt5Connector.sendMessage({
            action: 'delete_user_template',
            template_id: templateId
        });

        if (response && response.success) {
            showSuccess(`"${templateName}" silindi!`);
            // Refresh gallery
            showTemplateGallery();
        } else {
            showError('Silme başarısız');
        }
    } catch (e) {
        showError('Hata: ' + e.message);
    }
}

// Make functions global
window.showTemplateGallery = showTemplateGallery;
window.closeTemplateGallery = closeTemplateGallery;
window.selectTemplateFromGallery = selectTemplateFromGallery;
window.selectUserTemplate = selectUserTemplate;
window.deleteUserTemplate = deleteUserTemplate;

// ============================================
// BACKEND HANDLERS (for start_server.py)
// ============================================

// Add these handlers to start_server.py:
/*
elif action == 'start_conversation':
    from conversation_manager import ConversationManager
    if not hasattr(self, 'conv_manager'):
        self.conv_manager = ConversationManager()
    
    session_id = data.get('session_id')
    description = data.get('description')
    question = self.conv_manager.start_conversation(session_id, description)
    
    await websocket.send(json.dumps({
        'type': 'conversation_question',
        'data': {'question': question}
    }))

elif action == 'answer_question':
    session_id = data.get('session_id')
    question_id = data.get('question_id')
    answer = data.get('answer')
    
    self.conv_manager.process_answer(session_id, question_id, answer)
    next_question = self.conv_manager.get_next_question(session_id)
    
    if next_question:
        await websocket.send(json.dumps({
            'type': 'conversation_question',
            'data': {'question': next_question}
        }))
    else:
        await websocket.send(json.dumps({
            'type': 'conversation_complete',
            'data': {}
        }))

elif action == 'generate_final_prompt':
    session_id = data.get('session_id')
    prompt = self.conv_manager.generate_final_prompt(session_id)
    
    await websocket.send(json.dumps({
        'type': 'final_prompt',
        'data': {'prompt': prompt}
    }))

elif action == 'optimize_strategy':
    from strategy_optimizer import StrategyOptimizer
    optimizer = StrategyOptimizer()
    
    strategy_code = data.get('strategy_code')
    backtest_results = data.get('backtest_results')
    
    suggestions = optimizer.analyze_backtest(strategy_code, backtest_results)
    
    await websocket.send(json.dumps({
        'type': 'optimization_suggestions',
        'data': {'suggestions': suggestions}
    }))
*/
