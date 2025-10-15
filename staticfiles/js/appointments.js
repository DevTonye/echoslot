// Load today's appointments by default when page loads
document.addEventListener('DOMContentLoaded', function() {
    htmx.ajax('GET', 'today-appointments/', {
        target: '#appointment-content',
        swap: 'innerHTML'
    });
});

// Add custom HTMX event listeners for better UX
document.body.addEventListener('htmx:beforeRequest', function(evt) {
    const target = document.querySelector(evt.detail.target);
    if (target) {
        target.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner"></i>
                <p>Loading appointments...</p>
            </div>
        `;
    }
});

document.body.addEventListener('htmx:responseError', function(evt) {
    const target = document.querySelector(evt.detail.target);
    if (target) {
        target.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error loading appointments. Please try again.</p>
                <button class="btn btn-outline-primary mt-3" onclick="location.reload()">
                    <i class="fas fa-refresh"></i> Retry
                </button>
            </div>
        `;
    }
});