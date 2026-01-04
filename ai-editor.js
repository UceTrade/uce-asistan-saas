/**
 * Iterative AI Strategy Editing - IMPROVED
 */

let editHistory = [];

async function improveStrategy() {
    const request = document.getElementById('aiEditRequest').value;
    const currentCode = document.getElementById('strategyCode').value;

    if (!request.trim()) {
        showError('Lütfen bir iyileştirme isteği girin');
        return;
    }

    if (!currentCode.trim()) {
        showError('Önce bir strateji oluşturun');
        return;
    }

    // Show loading
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '⏳ İyileştiriliyor...';

    try {
        // Load AI settings
        const provider = loadFromStorage('aiProvider', 'groq');
        const apiKey = loadFromStorage('aiApiKey', '');

        if (!apiKey) {
            showError('Lütfen Ayarlar panelinden API anahtarınızı girin');
            btn.disabled = false;
            btn.textContent = '✨ İyileştir';
            return;
        }

        // IMPROVED: Better prompt for code modification
        const improvementPrompt = `Sen bir Python trading stratejisi kod editörüsün. Aşağıdaki mevcut kodu kullanıcının isteğine göre değiştir.

MEVCUT KOD:
${currentCode}

KULLANICI İSTEĞİ: ${request}

ÖNEMLİ KURALLAR:
1. Sadece değiştirilmiş Python kodunu döndür
2. Markdown kullanma, açıklama yapma
3. Fonksiyon adı 'strategy(data, position)' olarak kalsın
4. Tüm değerleri .iloc[-1] ile kontrol et
5. Tam çalışır Python kodu ver`;

        console.log('[AI EDIT] Request:', request);
        console.log('[AI EDIT] Sending to AI...');

        // Send to AI with proper credentials
        const response = await mt5Connector.sendMessage({
            action: 'parse_strategy',
            description: improvementPrompt,
            ai_provider: provider,
            api_key: apiKey
        });

        console.log('[AI EDIT] Response received:', response);

        if (response && response.code && response.code.trim()) {
            // Update code
            document.getElementById('strategyCode').value = response.code;

            // Add to history
            editHistory.push({
                request: request,
                timestamp: new Date().toLocaleTimeString('tr-TR'),
                previousCode: currentCode,
                newCode: response.code
            });

            // Show history (if element exists)
            if (document.getElementById('editHistory')) {
                updateEditHistory();
            }

            // Clear input
            document.getElementById('aiEditRequest').value = '';

            showSuccess('✅ Strateji iyileştirildi! Kodu kontrol edin.');
        } else {
            console.error('[AI EDIT] No code in response. Full response:', response);
            showError('AI kod döndürmedi. Lütfen isteğinizi daha açık yazın. Örn: "Stop loss 50 pip ekle"');
        }
    } catch (error) {
        console.error('[AI EDIT] Error:', error);
        showError('Hata: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '✨ İyileştir';
    }
}

function updateEditHistory() {
    const historyContainer = document.getElementById('editHistory');
    const historyList = document.getElementById('editHistoryList');

    if (!historyContainer || !historyList) return;

    if (editHistory.length === 0) {
        historyContainer.style.display = 'none';
        return;
    }

    historyContainer.style.display = 'block';

    historyList.innerHTML = editHistory.map((edit, index) => `
        <div class="mb-sm p-sm" style="background: rgba(0,0,0,0.2); border-radius: 4px; border-left: 3px solid #667eea;">
            <div class="flex justify-between items-center mb-xs">
                <strong class="text-sm">${edit.timestamp}</strong>
                <button class="btn btn-sm btn-outline" onclick="revertEdit(${index})" style="padding: 2px 8px; font-size: 11px;">
                    ↶ Geri Al
                </button>
            </div>
            <div class="text-sm text-secondary">"${edit.request}"</div>
        </div>
    `).reverse().join('');
}

function revertEdit(index) {
    if (index < 0 || index >= editHistory.length) return;

    const edit = editHistory[index];

    // Revert to previous code
    document.getElementById('strategyCode').value = edit.previousCode;

    // Remove this and all subsequent edits
    editHistory = editHistory.slice(0, index);

    updateEditHistory();
    showSuccess('✅ Değişiklik geri alındı');
}

// Add Enter key support
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('aiEditRequest');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                improveStrategy();
            }
        });
    }
});


async function mutateStrategy() {
    const currentCode = document.getElementById('strategyCode').value;
    const btn = document.getElementById('mutateBtn');

    if (!currentCode.trim()) {
        showError('Önce bir strateji oluşturun');
        return;
    }

    // Load AI settings - use the correct key names that match AIEngine
    // AIEngine uses 'aiProvider' and 'aiApiKey' via loadFromStorage
    const provider = loadFromStorage('aiProvider', 'groq');
    const apiKey = loadFromStorage('aiApiKey', '');

    if (!apiKey) {
        showError('Lütfen Ayarlar panelinden API anahtarınızı girin');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '🧬 MUTASYON BAŞLATILDI...';

    try {
        const response = await window.mt5Connector.sendMessage({
            action: 'evolve_strategy',
            code: currentCode,
            ai_provider: provider,
            api_key: apiKey
        });

        if (response && response.success) {
            // Update code
            const previousCode = currentCode;
            document.getElementById('strategyCode').value = response.code;

            // Show summary in an alert or specialized area
            if (response.summary) {
                showInfo(`🧬 MUTASYON TAMAMLANDI: ${response.summary}`);
            }

            // Add to history
            editHistory.push({
                request: "Quantum Mutasyon (Auto-Evolution)",
                timestamp: new Date().toLocaleTimeString('tr-TR'),
                previousCode: previousCode,
                newCode: response.code
            });

            if (document.getElementById('editHistory')) {
                updateEditHistory();
            }

            // Also show the summary in the strategySummarySection if it exists
            const summaryDiv = document.getElementById('strategySummaryText');
            if (summaryDiv) {
                const section = document.getElementById('strategySummarySection');
                section.style.display = 'block';
                summaryDiv.innerHTML = `<p><strong>Evrimleşmiş Strateji Güncellemesi:</strong></p><p>${response.summary}</p>`;
            }

            showSuccess('✅ Strateji başarıyla mutasyona uğradı!');
        } else {
            showError('Mutasyon hatası: ' + (response.error || 'Bilinmeyen hata'));
        }
    } catch (e) {
        console.error("[EVOLUTION] Failed:", e);
        showError('Hata: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🧬 QUANTUM MUTASYON';
    }
}

// Add to window
window.mutateStrategy = mutateStrategy;
window.improveStrategy = improveStrategy;
window.revertEdit = revertEdit;
