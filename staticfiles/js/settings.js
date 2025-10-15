// Load profile by default when page loads
    document.addEventListener('DOMContentLoaded', function () {
        htmx.ajax('GET', settingsProfileurl, {
            target: '#setting-content',
            swap: 'innerHTML'
        });
    });

    document.body.addEventListener('htmx:configRequest', function (event) {
        event.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
    });