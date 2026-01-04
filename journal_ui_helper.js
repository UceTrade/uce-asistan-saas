/**
 * Helper for Journal UI interactions
 */

window.analyzeJournal = async () => {
    if (!journal.currentData || !journal.currentData.history) {
        showError('Analiz için önce günlük verilerinin yüklenmesi gerekiyor.');
        return;
    }

    const outputEl = document.getElementById('journalAIAnalysis');
    if (!outputEl) return;

    outputEl.innerHTML = '<div class="text-center" style="padding: 2rem;"><div class="text-primary text-xl mb-sm">🧠</div><div>YZ Koç verilerinizi inceliyor...</div></div>';

    try {
        const analysis = await aiEngine.analyzeJournal(journal.currentData);

        // Simple Markdown cleaning for display
        let formatted = analysis
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
            .replace(/### (.*?)\n/g, '<h3 class="mb-sm mt-md text-primary">$1</h3>') // Headers
            .replace(/- (.*?)\n/g, '<li class="ml-md">$1</li>') // List items
            .replace(/\n/g, '<br>'); // Line breaks

        outputEl.innerHTML = `<div class="ai-analysis-content">${formatted}</div>`;

    } catch (err) {
        console.error(err);
        outputEl.innerHTML = '<div class="text-danger">Analiz sırasında bir hata oluştu. Lütfen tekrar deneyin.</div>';
    }
};
