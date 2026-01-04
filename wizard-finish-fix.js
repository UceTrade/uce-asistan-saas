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

**IMPORTANT - ATR-Based Stop Loss Implementation:**
1. Calculate ATR(14): atr = (data['high'] - data['low']).rolling(14).mean()
2. Stop Loss Distance: ${slMultiplier} * ATR
3. For LONG positions: stop_loss = entry_price - (${slMultiplier} * atr.iloc[-1])
4. For SHORT positions: stop_loss = entry_price + (${slMultiplier} * atr.iloc[-1])

Please generate a strategy with these preferences and ATR-based stop loss logic.`;

    // Close wizard
    closeConversationWizard();

    // Fill description
    document.getElementById('strategyDescription').value = enhancedPrompt;

    // Auto-generate
    showSuccess('✨ Gelişmiş prompt oluşturuldu! ATR bazlı stop loss eklenecek.');
    setTimeout(() => generateStrategy(), 500);
}
