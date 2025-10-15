// Load profile by default when page loads
    document.addEventListener('DOMContentLoaded', function () {
        htmx.ajax('GET', profilesettings, {
            target: '#setting-content',
            swap: 'innerHTML'
        });
    });

    document.body.addEventListener('htmx:configRequest', function(evt) {
        evt.detail.parameters['X-CSRFToken'] = '{{ csrf_token }}'; 
});