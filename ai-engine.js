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

// Create global instance
const aiEngine = new AIEngine();
