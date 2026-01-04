/**
 * Journal Module - Trade logging and analysis
 */

class Journal {
    constructor() {
        this.currentData = null;
        this.currentPositionId = null;
    }

    /**
     * Load journal data from backend
     */
    loadJournalData(days = 30) {
        if (!mt5Connector || !mt5Connector.connected) {
            showError('MT5 sunucusuna bağlı değilsiniz.');
            return;
        }

        // Show loading state
        const tbody = document.getElementById('journalTableBody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding: 2rem;">Veriler yükleniyor...</td></tr>';
        }

        mt5Connector.send('get_journal_data', { days: parseInt(days) });
    }

    /**
     * Handle incoming journal data
     */
    displayJournalData(response) {
        const { history, stats } = response.data;
        this.currentData = { history, stats };

        // Update Stats
        setText('jTotalTrades', stats.total_trades);
        setText('jWinRate', stats.win_rate + '%');
        setText('jProfitFactor', stats.profit_factor);

        const netProfitEl = document.getElementById('jNetProfit');
        if (netProfitEl) {
            netProfitEl.textContent = formatCurrency(stats.net_profit);
            netProfitEl.className = `stat-value ${stats.net_profit >= 0 ? 'stat-positive' : 'stat-negative'}`;
        }

        setText('jBestPair', stats.best_pair);
        setText('jAvgWin', formatCurrency(stats.avg_win));
        setText('jAvgLoss', formatCurrency(stats.avg_loss));

        // Update Table
        this.renderTable(history);
    }

    /**
     * Render trade history table
     */
    renderTable(trades) {
        const tbody = document.getElementById('journalTableBody');
        if (!tbody) return;

        if (!trades || trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="padding: 2rem;">Bu tarih aralığında işlem bulunamadı.</td></tr>';
            return;
        }

        const emotions = {
            'calm': '😌 Sakin',
            'anxious': '😰 Endişeli',
            'greedy': '🤑 Açgözlü',
            'revenge': '😡 İntikam',
            'fearful': '😨 Korkulu',
            'confident': '😎 Özgüvenli',
            'neutral': '😐 Nötr'
        };

        tbody.innerHTML = trades.map(trade => {
            const date = new Date(trade.time).toLocaleString('tr-TR');
            const isProfit = trade.profit >= 0;
            const profitClass = isProfit ? 'text-success' : 'text-danger';
            const profitSign = isProfit ? '+' : '';

            // Format notes/tags
            let noteDisplay = '';
            if (trade.strategy) {
                noteDisplay += `<span class="badge badge-info">${trade.strategy}</span> `;
            }
            if (trade.emotion && trade.emotion !== 'neutral') {
                noteDisplay += `<span class="badge badge-warning">${emotions[trade.emotion] || trade.emotion}</span> `;
            }
            if (trade.note) {
                const shortNote = trade.note.length > 30 ? trade.note.substring(0, 30) + '...' : trade.note;
                noteDisplay += `<div class="text-sm text-secondary mt-xs">${shortNote}</div>`;
            }

            return `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 1rem;">${date}</td>
                    <td style="padding: 1rem; font-weight: 600;">${trade.symbol}</td>
                    <td style="padding: 1rem;">
                        <span class="badge ${trade.type === 'BUY' ? 'badge-success' : 'badge-danger'}">${trade.type}</span>
                    </td>
                    <td style="padding: 1rem; font-weight: 600;" class="${profitClass}">
                        ${profitSign}${formatCurrency(trade.profit)}
                    </td>
                    <td style="padding: 1rem;">
                        ${noteDisplay || '<span class="text-muted text-sm">-</span>'}
                    </td>
                    <td style="padding: 1rem;">
                        <button class="btn btn-outline btn-sm" onclick="openNoteModal('${trade.position_id}')">
                            ✏️ Not Ekle
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    /**
     * Open note editor modal for a specific trade
     */
    openNoteModal(positionId) {
        this.currentPositionId = positionId;
        const trade = this.currentData.history.find(t => t.position_id === positionId);

        if (!trade) return;

        // Populate fields
        document.getElementById('notePositionId').value = positionId;
        document.getElementById('noteStrategy').value = trade.strategy || '';
        document.getElementById('noteText').value = trade.note || '';

        // Use existing setEmotion logic from utility/inline
        this.setEmotion(trade.emotion || 'neutral');

        const modal = document.getElementById('noteModal');
        modal.classList.add('active');
    }

    setEmotion(emotion) {
        document.getElementById('noteEmotion').value = emotion;

        // Visual update
        document.querySelectorAll('.emotion-btn').forEach(btn => {
            if (btn.dataset.val === emotion) {
                btn.classList.add('btn-primary');
                btn.classList.remove('btn-outline');
            } else {
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-outline');
            }
        });
    }

    /**
     * Save the note to backend
     */
    saveNote(event) {
        event.preventDefault();

        const positionId = document.getElementById('notePositionId').value;
        const noteData = {
            emotion: document.getElementById('noteEmotion').value,
            strategy: document.getElementById('noteStrategy').value,
            note: document.getElementById('noteText').value
        };

        mt5Connector.send('save_trade_note', {
            position_id: positionId,
            data: noteData
        });

        // Close modal
        document.getElementById('noteModal').classList.remove('active');
    }

    onNoteSaved(success) {
        if (success) {
            showSuccess('Not başarıyla kaydedildi!');
            // Reload data to reflect changes
            this.loadJournalData();
        } else {
            showError('Hata: Not kaydedilemedi.');
        }
    }
}

// Create instance
const journal = new Journal();

// Global Functions for HTML
window.loadJournalData = (days) => journal.loadJournalData(days);
window.openNoteModal = (id) => journal.openNoteModal(id);
window.closeNoteModal = () => document.getElementById('noteModal').classList.remove('active');
window.saveTradeNote = (e) => journal.saveNote(e);

// Emotion selector handler
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.emotion-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            journal.setEmotion(e.target.dataset.val);
        });
    });
});
