// Function to handle tab switching
function setActiveTab(clickedTab) {
    // Remove active class from all tabs
    document.querySelectorAll('.tab-button').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Add active class to clicked tab
    clickedTab.classList.add('active');
}

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