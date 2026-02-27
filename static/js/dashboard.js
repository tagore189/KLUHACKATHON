/**
 * dashboard.js
 * Handles dashboard interactivity, tab switching, and dynamic filtering.
 */

document.addEventListener('DOMContentLoaded', () => {
    initDashboardTabs();
});

function initDashboardTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    const cards = document.querySelectorAll('.scan-card');

    if (!tabs.length) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active tab state
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const filterType = tab.textContent.toLowerCase();

            cards.forEach(card => {
                const statusBadge = card.querySelector('.status-badge');
                if (!statusBadge) return;

                const status = statusBadge.textContent.trim().toLowerCase();

                if (filterType.includes('all scans')) {
                    card.style.display = 'block';
                } else if (filterType.includes('completed') && status === 'completed') {
                    card.style.display = 'block';
                } else if (filterType.includes('under review') && status === 'under review') {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });

            // Smooth entrance for filtered cards
            const visibleCards = Array.from(cards).filter(c => c.style.display !== 'none');
            visibleCards.forEach((c, i) => {
                c.style.opacity = '0';
                c.style.transform = 'translateY(10px)';
                setTimeout(() => {
                    c.style.transition = 'all 0.3s ease';
                    c.style.opacity = '1';
                    c.style.transform = 'translateY(0)';
                }, i * 50);
            });
        });
    });
}
