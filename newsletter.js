/**
 * UceAsistan Newsletter & Email Collection System
 * Collects user emails for marketing and sends to backend
 */

class NewsletterSystem {
    constructor() {
        this.apiEndpoint = '/api/newsletter';
        this.storageKey = 'uce_newsletter_subscribed';
    }

    /**
     * Check if user already subscribed
     */
    isSubscribed() {
        return localStorage.getItem(this.storageKey) === 'true';
    }

    /**
     * Subscribe email to newsletter
     */
    async subscribe(email, source = 'landing') {
        if (!this.validateEmail(email)) {
            return { success: false, error: 'Geçersiz e-posta adresi' };
        }

        try {
            // For now, store locally and log (in production, send to backend)
            const subscriptionData = {
                email,
                source,
                subscribedAt: new Date().toISOString(),
                userAgent: navigator.userAgent,
                referrer: document.referrer || 'direct'
            };

            // Store in localStorage for demo
            const subscribers = JSON.parse(localStorage.getItem('uce_subscribers') || '[]');

            // Check if already exists
            if (subscribers.some(s => s.email === email)) {
                return { success: false, error: 'Bu e-posta zaten kayıtlı' };
            }

            subscribers.push(subscriptionData);
            localStorage.setItem('uce_subscribers', JSON.stringify(subscribers));
            localStorage.setItem(this.storageKey, 'true');

            // In production, send to backend
            // await fetch(this.apiEndpoint, {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json' },
            //     body: JSON.stringify(subscriptionData)
            // });

            console.log('Newsletter subscription:', subscriptionData);

            return { success: true, message: 'Başarıyla abone oldunuz!' };
        } catch (error) {
            console.error('Newsletter subscription error:', error);
            return { success: false, error: 'Bir hata oluştu, lütfen tekrar deneyin' };
        }
    }

    /**
     * Validate email format
     */
    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    /**
     * Get all subscribers (for admin)
     */
    getSubscribers() {
        return JSON.parse(localStorage.getItem('uce_subscribers') || '[]');
    }

    /**
     * Export subscribers as CSV
     */
    exportCSV() {
        const subscribers = this.getSubscribers();
        if (subscribers.length === 0) return null;

        const headers = ['Email', 'Source', 'Subscribed At'];
        const rows = subscribers.map(s => [s.email, s.source, s.subscribedAt]);

        const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
        return csv;
    }

    /**
     * Download subscribers as CSV file
     */
    downloadCSV() {
        const csv = this.exportCSV();
        if (!csv) {
            alert('Henüz abone yok');
            return;
        }

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `uceasistan_subscribers_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    }
}

// Initialize global instance
window.newsletter = new NewsletterSystem();

/**
 * Handle newsletter form submission
 */
function handleNewsletterSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const emailInput = form.querySelector('input[type="email"]');
    const submitBtn = form.querySelector('button[type="submit"]');
    const email = emailInput.value.trim();

    if (!email) return;

    // Disable button and show loading
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '⏳ Gönderiliyor...';
    submitBtn.disabled = true;

    window.newsletter.subscribe(email, 'newsletter_form').then(result => {
        if (result.success) {
            submitBtn.innerHTML = '✅ Abone Olundu!';
            submitBtn.style.background = 'var(--gradient-success)';
            emailInput.value = '';

            // Reset after 3 seconds
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.style.background = '';
                submitBtn.disabled = false;
            }, 3000);
        } else {
            submitBtn.innerHTML = '❌ ' + result.error;
            submitBtn.style.background = 'var(--danger)';

            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.style.background = '';
                submitBtn.disabled = false;
            }, 2000);
        }
    });
}
