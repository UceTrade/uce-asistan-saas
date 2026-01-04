/**
 * Strategy Manager UI Helper
 * Handles saving, loading, and executing strategies
 */

class StrategyManagerUI {
    constructor() {
        this.strategies = [];
        this.currentStrategyId = null;

        // Bind events
        this.initEventListeners();
    }

    initEventListeners() {
        // Try to setup UI immediately if document is ready
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            this.setupUI();
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupUI();
            });
        }

        // Retry setup periodically in case elements are added dynamically
        setInterval(() => this.setupUI(), 2000);

        // Listen for backend messages
        window.addEventListener('mt5_event', (e) => {
            const data = e.detail;
            if (data.type === 'strategy_saved') {
                if (data.success) {
                    alert('Strateji başarıyla kaydedildi! ✅');
                    this.loadStrategies(); // Refresh list
                } else {
                    alert('Hata: Strateji kaydedilemedi ❌');
                }
            } else if (data.type === 'strategies_list') {
                this.strategies = data.data;
                this.renderStrategiesList();
            } else if (data.type === 'auto_trade_started') {
                if (data.success) {
                    alert('Otomatik İşlem Başlatıldı! 🤖💰\nRobot arka planda çalışıyor.');
                    document.getElementById('startAutoTradeBtn').innerHTML = '<i class="fas fa-stop"></i> Durdur';
                    document.getElementById('startAutoTradeBtn').classList.replace('btn-success', 'btn-danger');
                    document.getElementById('startAutoTradeBtn').onclick = () => this.stopAutoTrade();
                } else {
                    alert('Hata: ' + data.message);
                }
            } else if (data.type === 'auto_trade_stopped') {
                alert('Otomatik İşlem Durduruldu. 🛑');
                this.updateAutoTradeButton(false);
            }
        });
    }

    setupUI() {
        // Add "Save Strategy" button to generated code section
        const codeSection = document.getElementById('generatedCodeSection');
        if (codeSection) {
            const btnGroup = codeSection.querySelector('.btn-group') || codeSection.querySelector('.d-flex');

            if (btnGroup && !document.getElementById('saveStrategyBtn')) {
                const saveBtn = document.createElement('button');
                saveBtn.id = 'saveStrategyBtn';
                saveBtn.className = 'btn btn-info ml-2';
                saveBtn.innerHTML = '<i class="fas fa-save"></i> Kaydet';
                saveBtn.onclick = () => this.saveCurrentStrategy();
                btnGroup.appendChild(saveBtn);
            }

            // Add "Auto Trade" button
            if (btnGroup && !document.getElementById('autoTradeBtn')) {
                const autoBtn = document.createElement('button');
                autoBtn.id = 'autoTradeBtn';
                autoBtn.className = 'btn btn-success ml-2';
                autoBtn.innerHTML = '<i class="fas fa-robot"></i> Otomatik İşlem';
                autoBtn.onclick = () => this.showExecutionModal();
                btnGroup.appendChild(autoBtn);
            }
        }
    }

    saveCurrentStrategy() {
        const code = document.getElementById('strategyCode').value;
        const summary = document.getElementById('strategySummaryText')?.textContent || "Özet yok";

        if (!code) {
            alert('Kaydedilecek strateji kodu bulunamadı!');
            return;
        }

        const name = prompt("Strateji Adı Giriniz:", "Yeni Strateji " + new Date().toLocaleDateString());
        if (!name) return;

        const timeframe = document.getElementById('timeframe')?.value || "H1";

        mt5Connector.send({
            action: 'save_strategy',
            name: name,
            code: code,
            summary: summary,
            timeframe: timeframe
        });
    }

    loadStrategies() {
        mt5Connector.send({ action: 'get_strategies' });
    }

    renderStrategiesList() {
        const tbody = document.getElementById('strategiesTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (this.strategies.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">Henüz kayıtlı strateji yok.</td></tr>';
            return;
        }

        this.strategies.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${s.name}</strong></td>
                <td>${new Date(s.created_at).toLocaleString('tr-TR')}</td>
                <td><span class="badge badge-info">${s.timeframe || 'N/A'}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="strategyManager.loadToEditor(${s.id})">
                        <i class="fas fa-edit"></i> Düzenle
                    </button>
                    <button class="btn btn-sm btn-success" onclick="strategyManager.quickExecute(${s.id})">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="strategyManager.deleteStrategy(${s.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    loadToEditor(id) {
        const s = this.strategies.find(x => x.id === id);
        if (!s) return;

        // Switch to Backtest View
        switchView('backtest');

        // Fill editor
        const codeTextarea = document.getElementById('strategyCode');
        codeTextarea.value = s.code;

        const summarySection = document.getElementById('strategySummarySection');
        const summaryText = document.getElementById('strategySummaryText');

        if (summarySection && summaryText) {
            summaryText.textContent = s.summary;
            summarySection.style.display = 'block';
        }
    }

    deleteStrategy(id) {
        if (confirm('Bu stratejiyi silmek istediğinize emin misiniz?')) {
            mt5Connector.send({
                action: 'delete_strategy',
                id: id
            });
            // Optimistic update
            this.strategies = this.strategies.filter(s => s.id !== id);
            this.renderStrategiesList();
        }
    }

    quickExecute(id) {
        this.loadToEditor(id);
        this.showExecutionModal();
    }

    showExecutionModal() {
        const code = document.getElementById('strategyCode').value;
        if (!code) {
            alert('Lütfen önce bir strateji seçin veya oluşturun.');
            return;
        }

        // Create modal HTML if doesn't exist
        if (!document.getElementById('executionModal')) {
            const modal = document.createElement('div');
            modal.id = 'executionModal';
            modal.className = 'modal fade';
            modal.tabIndex = -1;
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-success text-white">
                            <h5 class="modal-title">🤖 Otomatik İşlem Başlat</h5>
                            <button type="button" class="close text-white" data-dismiss="modal">&times;</button>
                        </div>
                        <div class="modal-body">
                            <div class="form-group">
                                <label>Sembol</label>
                                <input type="text" id="execSymbol" class="form-control" value="XAUUSD">
                            </div>
                            <div class="form-group">
                                <label>Zaman Dilimi</label>
                                <select id="execTimeframe" class="form-control">
                                    <option value="M1">M1</option>
                                    <option value="M5">M5</option>
                                    <option value="M15">M15</option>
                                    <option value="M30">M30</option>
                                    <option value="H1" selected>H1</option>
                                    <option value="H4">H4</option>
                                    <option value="D1">D1</option>
                                </select>
                            </div>
                            <div class="row">
                                <div class="col-6">
                                    <div class="form-group">
                                        <label>Risk/Ödül Oranı (R:R)</label>
                                        <input type="number" id="execRR" class="form-control" value="2.0" step="0.1">
                                        <small class="form-text text-muted">Örn: 1 birim risk için 2 birim kar hedefle.</small>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="form-group">
                                        <label>Lot Büyüklüğü</label>
                                        <input type="number" id="execLot" class="form-control" value="0.01" step="0.01">
                                    </div>
                                </div>
                            </div>
                            <div class="alert alert-warning">
                                <i class="fas fa-exclamation-triangle"></i> 
                                <strong>DİKKAT:</strong> Robot, Price Action (Swing Low/High) kullanarak otomatik Stop Loss belirleyecektir.
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>
                            <button type="button" class="btn btn-success" id="startAutoTradeBtn" onclick="strategyManager.startAutoTrade()">
                                <i class="fas fa-rocket"></i> Başlat
                            </button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        $('#executionModal').modal('show');
    }

    startAutoTrade() {
        const symbol = document.getElementById('execSymbol').value;
        const timeframe = document.getElementById('execTimeframe').value;
        const rr = document.getElementById('execRR').value;
        const lot = document.getElementById('execLot').value;
        const code = document.getElementById('strategyCode').value;

        mt5Connector.send({
            action: 'start_auto_trade',
            code: code,
            symbol: symbol,
            timeframe: timeframe,
            rr_ratio: rr,
            lot_size: lot
        });

        $('#executionModal').modal('hide');
    }

    updateAutoTradeButton(isRunning) {
        const btn = document.getElementById('startAutoTradeBtn') || document.getElementById('autoTradeBtn');
        if (!btn) return;

        if (isRunning) {
            btn.innerHTML = '<i class="fas fa-stop"></i> Durdur';
            btn.classList.replace('btn-success', 'btn-danger');
            btn.onclick = () => this.stopAutoTrade();
        } else {
            btn.innerHTML = '<i class="fas fa-robot"></i> Otomatik İşlem';
            if (btn.classList.contains('btn-danger')) {
                btn.classList.replace('btn-danger', 'btn-success');
            }
            btn.onclick = () => this.showExecutionModal();
        }
    }
}

// Initialize Global Instance
const strategyManager = new StrategyManagerUI();
