/**
 * AI Engine - Multi-provider AI integration with personality system
 */

class AIEngine {
    constructor() {
        this.provider = 'groq'; // default
        this.apiKey = '';
        this.conversationHistory = new Map(); // per account
        this.currentAccountId = null;
        this.personalities = {
            motivational: {
                name: 'Motivasyon Koçu',
                emoji: '🔥',
                systemPrompt: 'Sen hevesli bir yatırım koçusun. Yatırımcı kazanırken onları motive et ve özgüvenlerini artır. Yanıtlarını kısa, enerjik tut ve TÜRKÇE konuş.\n\nEğer kullanıcı "X al", "Y sat", "Z lot işlem gir" gibi emirler verirse, yanıtına ŞU JSON FORMATINI GİZLİCE EKLE:\n[[TRADE_ACTION]] {"symbol": "SEMBOL", "action": "BUY/SELL", "volume": 0.0, "sl_percent": 0.0, "rr": 0.0}\n\nEğer kullanıcı "BÜTÜN İŞLEMLERİ KAPAT" derse:\n[[TRADE_ACTION]] {"symbol": "ALL", "action": "CLOSE_ALL", "volume": 0, "sl_percent": 0, "rr": 0}\n\nEğer kullanıcı "EURUSD %50 kar al", "yarısını kapat" derse:\n[[TRADE_ACTION]] {"symbol": "EURUSD", "action": "CLOSE_PARTIAL", "percent": 50}'
            },
            risk_guardian: {
                name: 'Risk Koruyucu',
                emoji: '⚠️',
                systemPrompt: 'Sen disiplinli bir risk yönetimi danışmanısın. Risk seviyeleri yükseldiğinde yatırımcıyı sıkı ama destekleyici bir şekilde uyar. Sermayelerini korumaya odaklan ve TÜRKÇE konuş.\n\nEğer kullanıcı "X al", "Y sat", "Z lot işlem gir" gibi emirler verirse, önce risk uyarısı yap ama SONRA ŞU JSON FORMATINI EKLEREK işlemi onayla:\n[[TRADE_ACTION]] {"symbol": "SEMBOL", "action": "BUY/SELL", "volume": 0.0, "sl_percent": 0.0, "rr": 0.0}\n\nEğer kullanıcı "BÜTÜN İŞLEMLERİ KAPAT" derse:\n[[TRADE_ACTION]] {"symbol": "ALL", "action": "CLOSE_ALL", "volume": 0, "sl_percent": 0, "rr": 0}\n\nEğer kullanıcı "EURUSD %50 kar al", "yarısını kapat" derse:\n[[TRADE_ACTION]] {"symbol": "EURUSD", "action": "CLOSE_PARTIAL", "percent": 50}'
            },
            analytical: {
                name: 'Analitik Danışman',
                emoji: '📊',
                systemPrompt: 'Sen objektif bir yatırım analistisin. Veriye dayalı içgörüler ve stratejik öneriler sun. Profesyonel, net ol ve TÜRKÇE konuş.\n\nEğer kullanıcı "X al", "Y sat", "Z lot işlem gir" gibi emirler verirse, analizini yap ve SONUNA ŞU JSON FORMATINI EKLE:\n[[TRADE_ACTION]] {"symbol": "SEMBOL", "action": "BUY/SELL", "volume": 0.0, "sl_percent": 0.0, "rr": 0.0}\n\nÖnemli: Eğer stop loss belirtilmezse varsayılan 0.5, RR belirtilmezse varsayılan 1.5 kullan.\n\nEğer kullanıcı "BÜTÜN İŞLEMLERİ KAPAT" derse:\n[[TRADE_ACTION]] {"symbol": "ALL", "action": "CLOSE_ALL", "volume": 0, "sl_percent": 0, "rr": 0}\n\nEğer kullanıcı "EURUSD %50 kar al", "yarısını kapat" derse:\n[[TRADE_ACTION]] {"symbol": "EURUSD", "action": "CLOSE_PARTIAL", "percent": 50}'
            },
            psychological: {
                name: 'Psikolojik Destek',
                emoji: '🧘',
                systemPrompt: 'Sen bir yatırım psikoloğusun. Yatırımcı kaybederken sakin kalmalarına ve perspektiflerini korumalarına yardımcı ol. Duygusal destek sağla, zihinsel berraklık kazandır ve TÜRKÇE konuş.\n\nEğer kullanıcı işlem açmak isterse, duygusal durumunu sor ama yine de işlemi yapmak için ŞU JSON FORMATINI EKLE:\n[[TRADE_ACTION]] {"symbol": "SEMBOL", "action": "BUY/SELL", "volume": 0.0, "sl_percent": 0.0, "rr": 0.0}\n\nEğer kullanıcı "BÜTÜN İŞLEMLERİ KAPAT" derse:\n[[TRADE_ACTION]] {"symbol": "ALL", "action": "CLOSE_ALL", "volume": 0, "sl_percent": 0, "rr": 0}\n\nEğer kullanıcı "EURUSD %50 kar al", "yarısını kapat" derse:\n[[TRADE_ACTION]] {"symbol": "EURUSD", "action": "CLOSE_PARTIAL", "percent": 50}'
            }
        };
        this.loadSettings();
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        const provider = loadFromStorage('aiProvider', 'groq');
        const apiKey = loadFromStorage('aiApiKey', '');

        this.provider = provider;
        this.apiKey = apiKey ? apiKey.trim() : '';  // Trim whitespace
    }

    /**
     * Save settings to localStorage
     */
    saveSettings(provider, apiKey) {
        this.provider = provider;
        this.apiKey = apiKey ? apiKey.trim() : '';  // Trim whitespace

        saveToStorage('aiProvider', provider);
        saveToStorage('aiApiKey', apiKey ? apiKey.trim() : '');
    }

    /**
     * Get appropriate personality based on context
     */
    getPersonality(accountData, riskMetrics) {
        // Danger zone - use risk guardian
        if (riskMetrics && riskMetrics.riskLevel === 'danger') {
            return this.personalities.risk_guardian;
        }

        // Losing money - use psychological support
        if (accountData.daily_profit < 0 && Math.abs(accountData.daily_profit) > accountData.balance * 0.02) {
            return this.personalities.psychological;
        }

        // Winning - use motivational coach
        if (accountData.daily_profit > 0 && accountData.daily_profit > accountData.balance * 0.01) {
            return this.personalities.motivational;
        }

        // Default - analytical
        return this.personalities.analytical;
    }

    /**
     * Build context for AI
     */
    buildContext(accountData, riskMetrics, marketData = null) {
        const context = {
            balance: accountData.balance,
            equity: accountData.equity,
            profit: accountData.profit,
            daily_profit: accountData.daily_profit,
            positions_count: accountData.positions_count,
            drawdown: riskMetrics ? riskMetrics.currentDrawdown : 0,
            risk_level: riskMetrics ? riskMetrics.riskLevel : 'safe'
        };

        let contextStr = `Mevcut Yatırım Durumu:
- Bakiye: ${formatCurrency(context.balance)}
- Varlık: ${formatCurrency(context.equity)}
- Toplam K/Z: ${formatCurrency(context.profit)}
- Bugünkü K/Z: ${formatCurrency(context.daily_profit)}
- Açık Pozisyonlar: ${context.positions_count}
- Düşüş (Drawdown): %${context.drawdown.toFixed(2)}
- Risk Seviyesi: ${context.risk_level}`;

        if (marketData) {
            contextStr += `\n\nCANLI PIYASA ANALIZI (${marketData.symbol}):
- Fiyat: ${marketData.price}
- Değişim (24s): %${marketData.change_24h}
- RSI (14): ${marketData.rsi_14} (${marketData.rsi_14 > 70 ? 'Aşırı Alım' : marketData.rsi_14 < 30 ? 'Aşırı Satım' : 'Nötr'})
- SMA (20): ${marketData.sma_20}
- SMA (50): ${marketData.sma_50}
- Trend: ${marketData.trend === 'uptrend' ? 'Yükseliş ↗️' : marketData.trend === 'downtrend' ? 'Düşüş ↘️' : 'Nötr ➡️'}
- Zaman: ${marketData.timestamp}
Bu VERİLERİ kullanarak analiz yap. Eski verileri kullanma.`;
        }

        return contextStr;
    }

    /**
     * Send message to AI
     */
    async sendMessage(userMessage, accountData, riskMetrics, marketData = null) {
        if (!this.apiKey) {
            throw new Error('API anahtarı yapılandırılmamış. Lütfen Ayarlar kısmından ayarlayın.');
        }

        // Get appropriate personality
        const personality = this.getPersonality(accountData, riskMetrics);

        // Build context
        const context = this.buildContext(accountData, riskMetrics, marketData);

        // Get conversation history for this account
        const accountId = accountData.account_id || 'default';
        if (!this.conversationHistory.has(accountId)) {
            this.conversationHistory.set(accountId, []);
        }
        const history = this.conversationHistory.get(accountId);

        // Add user message to history
        history.push({
            role: 'user',
            content: userMessage
        });

        // Keep only last 10 messages
        if (history.length > 10) {
            history.splice(0, history.length - 10);
        }

        try {
            let response;
            const messages = [
                {
                    role: 'system',
                    content: `${personality.systemPrompt}\n\n${context}`
                },
                ...history
            ];

            if (this.provider === 'groq') {
                response = await this.callGroq(messages);
            } else if (this.provider === 'openai') {
                response = await this.callOpenAI(messages);
            } else if (this.provider === 'gemini') {
                response = await this.callGemini(messages);
            } else {
                throw new Error('Geçersiz YZ sağlayıcısı');
            }

            // Add AI response to history
            history.push({
                role: 'assistant',
                content: response
            });

            return {
                message: response,
                personality: personality.name,
                emoji: personality.emoji
            };

        } catch (error) {
            console.error('AI Error:', error);
            throw error;
        }
    }

    /**
     * Call Groq API
     */
    async callGroq(messages) {
        const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'llama-3.3-70b-versatile',
                messages: messages,
                max_tokens: 1500,
                temperature: 0.7
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'Groq API hatası');
        }

        const data = await response.json();
        return data.choices[0].message.content;
    }

    /**
     * Call OpenAI API
     */
    async callOpenAI(messages) {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'gpt-4-turbo-preview',
                messages: messages,
                max_tokens: 1500,
                temperature: 0.7
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'OpenAI API hatası');
        }

        const data = await response.json();
        return data.choices[0].message.content;
    }

    /**
     * Call Gemini API
     */
    async callGemini(messages) {
        // Extract system message and history from messages array
        const systemMsg = messages.find(m => m.role === 'system');
        const historyMsgs = messages.filter(m => m.role !== 'system');

        // Convert to Gemini format
        const contents = historyMsgs.map(msg => ({
            role: msg.role === 'assistant' ? 'model' : 'user',
            parts: [{ text: msg.content }]
        }));

        // Prepend system message as user context
        if (systemMsg) {
            contents.unshift({
                role: 'user',
                parts: [{ text: systemMsg.content }]
            });
        }

        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${this.apiKey}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                contents: contents,
                generationConfig: {
                    maxOutputTokens: 1500,
                    temperature: 0.7
                }
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'Gemini API hatası');
        }

        const data = await response.json();
        return data.candidates[0].content.parts[0].text;
    }

    /**
     * Clear conversation history for account
     */
    clearHistory(accountId) {
        this.conversationHistory.delete(accountId);
    }

    /**
     * Get proactive insight based on account state
     */
    getProactiveInsight(accountData, riskMetrics) {
        const personality = this.getPersonality(accountData, riskMetrics);

        const insights = {
            motivational: [
                `${personality.emoji} Harika iş! Bugün ${formatCurrency(accountData.daily_profit)} kârdasın. Bu momentumu koru!`,
                `${personality.emoji} Mükemmel gidiyorsun! Disiplininin karşılığını alıyorsun. Odaklanmaya devam et!`
            ],
            risk_guardian: [
                `${personality.emoji} Uyarı: %${riskMetrics.currentDrawdown.toFixed(2)} düşüştesin. İşlem büyüklüklerini azaltmayı düşün.`,
                `${personality.emoji} Risk uyarısı: Maksimum düşüş limitinin %${riskMetrics.drawdownUsed.toFixed(0)} kadarı kullanıldı. Dikkatli işlem yap!`
            ],
            psychological: [
                `${personality.emoji} Bugün ${formatCurrency(Math.abs(accountData.daily_profit))} zarardasın. Unutma, her işlemcinin kayıp günleri olur. Sakin kal ve planına sadık ol.`,
                `${personality.emoji} Gerekirse bir mola ver. Ruh halin, kayıpları hızlıca telafi etmekten daha önemli.`
            ],
            analytical: [
                `${personality.emoji} Güncel durum: ${accountData.positions_count} açık işlem, %${formatPercent(riskMetrics.currentDrawdown)} düşüş.`,
                `${personality.emoji} Hesap sağlığı: ${riskMetrics.riskLevel} bölge. Kalan günlük risk: ${formatCurrency(riskMetrics.remainingDailyRisk)}.`
            ]
        };

        const personalityKey = Object.keys(this.personalities).find(
            key => this.personalities[key].name === personality.name
        );

        const messages = insights[personalityKey] || insights.analytical;
        return messages[Math.floor(Math.random() * messages.length)];
    }
}

/**
 * FinAgent Client - Finance-specialized AI for trading decisions
 * Communicates with backend FinGPT integration for professional financial analysis
 * 
 * Supported FREE providers:
 * 1. Groq - FREE, no credit card required (console.groq.com)
 * 2. OpenRouter - 50 free requests/day (openrouter.ai)
 */
class FinAgentClient {
    constructor() {
        // Free providers (priority)
        this.groqApiKey = '';        // FREE - no credit card!
        this.openrouterApiKey = '';  // 50 free/day
        // Paid providers (fallback)
        this.togetherApiKey = '';
        this.fireworksApiKey = '';

        this.isEnabled = false;
        this.lastResponse = null;
        this.lastProviderUsed = null;
        this.loadSettings();
    }

    loadSettings() {
        this.groqApiKey = loadFromStorage('finAgentGroqKey', '');
        this.openrouterApiKey = loadFromStorage('finAgentOpenRouterKey', '');
        this.togetherApiKey = loadFromStorage('finAgentTogetherKey', '');
        this.fireworksApiKey = loadFromStorage('finAgentFireworksKey', '');
        this.isEnabled = loadFromStorage('finAgentEnabled', false);
    }

    saveSettings(groqKey, openrouterKey = '', togetherKey = '', fireworksKey = '', enabled = true) {
        this.groqApiKey = groqKey || '';
        this.openrouterApiKey = openrouterKey || '';
        this.togetherApiKey = togetherKey || '';
        this.fireworksApiKey = fireworksKey || '';
        this.isEnabled = enabled;

        saveToStorage('finAgentGroqKey', groqKey || '');
        saveToStorage('finAgentOpenRouterKey', openrouterKey || '');
        saveToStorage('finAgentTogetherKey', togetherKey || '');
        saveToStorage('finAgentFireworksKey', fireworksKey || '');
        saveToStorage('finAgentEnabled', enabled);
    }

    hasApiKey() {
        return !!(this.groqApiKey || this.openrouterApiKey || this.togetherApiKey || this.fireworksApiKey);
    }

    getActiveProvider() {
        if (this.groqApiKey) return 'Groq (Free)';
        if (this.openrouterApiKey) return 'OpenRouter (Free)';
        if (this.togetherApiKey) return 'Together AI';
        if (this.fireworksApiKey) return 'Fireworks AI';
        return 'None';
    }

    /**
     * Send query to FinAgent via WebSocket
     */
    async query(queryText, context = {}) {
        if (!this.hasApiKey()) {
            return {
                error: true,
                message: 'FinAgent API anahtarı gerekli. Groq ücretsiz! console.groq.com adresinden alabilirsiniz.',
                setup_required: true,
                setup_guide: '1. console.groq.com adresine gidin\n2. Ücretsiz hesap oluşturun (kredi kartı yok!)\n3. API Keys > Create API Key\n4. Konsolda: finAgent.saveSettings("YOUR_GROQ_KEY")'
            };
        }

        return new Promise((resolve, reject) => {
            if (!window.ws || window.ws.readyState !== WebSocket.OPEN) {
                reject(new Error('WebSocket bağlantısı yok'));
                return;
            }

            const handler = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'fin_agent_response') {
                        window.ws.removeEventListener('message', handler);
                        this.lastResponse = data.data;
                        resolve(data.data);
                    }
                } catch (e) {
                    // Not our message
                }
            };

            window.ws.addEventListener('message', handler);

            window.ws.send(JSON.stringify({
                action: 'fin_agent_query',
                query: queryText,
                context: context,
                api_keys: {
                    groq_api_key: this.groqApiKey,
                    openrouter_api_key: this.openrouterApiKey,
                    together_api_key: this.togetherApiKey,
                    fireworks_api_key: this.fireworksApiKey
                }
            }));

            // Timeout after 30s
            setTimeout(() => {
                window.ws.removeEventListener('message', handler);
                reject(new Error('FinAgent yanıt zaman aşımı'));
            }, 30000);
        });
    }

    /**
     * Get sentiment analysis for a symbol
     */
    async getSentiment(symbol, news = []) {
        return this._sendRequest('fin_agent_sentiment', {
            symbol: symbol,
            news: news
        }, 'fin_agent_sentiment_response');
    }

    /**
     * Get trading decision for a symbol
     */
    async getTradeSignal(symbol) {
        return this._sendRequest('fin_agent_trade_signal', {
            symbol: symbol
        }, 'fin_agent_trade_signal_response');
    }

    /**
     * Get risk assessment for planned trade
     */
    async assessRisk(symbol, lotSize) {
        return this._sendRequest('fin_agent_risk', {
            symbol: symbol,
            lot_size: lotSize
        }, 'fin_agent_risk_response');
    }

    /**
     * Get comprehensive market analysis
     */
    async analyzeMarket(symbol, timeframe = 'H1') {
        return this._sendRequest('fin_agent_analyze_market', {
            symbol: symbol,
            timeframe: timeframe
        }, 'fin_agent_market_analysis_response');
    }

    /**
     * Internal helper for sending requests
     */
    async _sendRequest(action, params, responseType) {
        if (!this.hasApiKey()) {
            return {
                error: true,
                message: 'FinAgent API anahtarı gerekli',
                setup_required: true
            };
        }

        return new Promise((resolve, reject) => {
            if (!window.ws || window.ws.readyState !== WebSocket.OPEN) {
                reject(new Error('WebSocket bağlantısı yok'));
                return;
            }

            const handler = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === responseType) {
                        window.ws.removeEventListener('message', handler);
                        resolve(data.data);
                    }
                } catch (e) {
                    // Not our message
                }
            };

            window.ws.addEventListener('message', handler);

            window.ws.send(JSON.stringify({
                action: action,
                ...params,
                api_keys: {
                    together_api_key: this.togetherApiKey,
                    fireworks_api_key: this.fireworksApiKey
                }
            }));

            // Timeout
            setTimeout(() => {
                window.ws.removeEventListener('message', handler);
                reject(new Error('İstek zaman aşımı'));
            }, 30000);
        });
    }

    /**
     * Format FinAgent response for display
     */
    formatResponse(response) {
        if (response.error) {
            return `❌ **Hata:** ${response.message}`;
        }

        const queryType = response.query_type;
        let formatted = '';

        switch (queryType) {
            case 'sentiment':
                formatted = this._formatSentiment(response);
                break;
            case 'trade_decision':
                formatted = this._formatTradeDecision(response);
                break;
            case 'risk':
                formatted = this._formatRisk(response);
                break;
            case 'analysis':
                formatted = this._formatAnalysis(response);
                break;
            default:
                formatted = response.summary_tr || JSON.stringify(response, null, 2);
        }

        return formatted;
    }

    _formatSentiment(r) {
        const emoji = r.sentiment === 'BULLISH' ? '🟢' : r.sentiment === 'BEARISH' ? '🔴' : '🟡';
        return `${emoji} **Sentiment: ${r.sentiment}** (Güven: %${(r.confidence * 100).toFixed(0)})

📊 **Etki Seviyesi:** ${r.impact_level || 'N/A'}
⏱️ **Zaman Dilimi:** ${r.timeframe || 'N/A'}

**Önemli Faktörler:**
${(r.key_factors || []).map(f => `• ${f}`).join('\n') || '• Bilgi yok'}

💬 ${r.summary_tr || ''}`;
    }

    _formatTradeDecision(r) {
        const emoji = r.decision === 'BUY' ? '🟢 LONG' : r.decision === 'SELL' ? '🔴 SHORT' : '⏸️ BEKLE';
        return `${emoji} **${r.decision}** (Güven: %${(r.confidence * 100).toFixed(0)})

📍 **Giriş Bölgesi:** ${r.entry_zone?.min || 'N/A'} - ${r.entry_zone?.max || 'N/A'}
🛑 **Stop Loss:** ${r.stop_loss || 'N/A'}
🎯 **Take Profit:** ${(r.take_profit || []).map(tp => `${tp.level} (${tp.ratio})`).join(', ') || 'N/A'}
⚖️ **Risk/Reward:** ${r.risk_reward || 'N/A'}

**Gerekçeler:**
${(r.reasoning || []).map(reason => `• ${reason}`).join('\n') || '• Bilgi yok'}

${(r.warnings || []).length > 0 ? `\n⚠️ **Uyarılar:**\n${r.warnings.map(w => `• ${w}`).join('\n')}` : ''}

💬 ${r.summary_tr || ''}`;
    }

    _formatRisk(r) {
        const riskEmoji = {
            'LOW': '🟢',
            'MEDIUM': '🟡',
            'HIGH': '🟠',
            'EXTREME': '🔴'
        };
        return `${riskEmoji[r.risk_level] || '⚪'} **Risk Seviyesi: ${r.risk_level}** (Skor: ${r.risk_score || 0}/100)

📊 **Önerilen Lot:** ${r.recommended_lot || 'N/A'}
📈 **Max Pozisyon:** ${r.max_position_size || 'N/A'}

**Risk Faktörleri:**
${(r.risk_factors || []).map(f => `• ${f}`).join('\n') || '• Bilgi yok'}

**Önlemler:**
${(r.mitigation || []).map(m => `• ${m}`).join('\n') || '• Bilgi yok'}

💬 ${r.summary_tr || ''}`;
    }

    _formatAnalysis(r) {
        const trendEmoji = r.trend === 'UPTREND' ? '📈' : r.trend === 'DOWNTREND' ? '📉' : '➡️';
        return `${trendEmoji} **Trend: ${r.trend}** (Güç: %${r.trend_strength || 0})

🎯 **Temel Seviyeler:**
• Direnç: ${(r.key_levels?.resistance || []).join(', ') || 'N/A'}
• Destek: ${(r.key_levels?.support || []).join(', ') || 'N/A'}

📊 **Teknik Sinyaller:**
${(r.technical_signals || []).map(s => `• ${s.indicator}: ${s.signal} (${s.value})`).join('\n') || '• Bilgi yok'}

🔮 **Genel Görünüm:** ${r.outlook || 'N/A'}

💬 ${r.summary_tr || ''}`;
    }
}

// Create global instances
const aiEngine = new AIEngine();
const finAgent = new FinAgentClient();
