// Handles initial notification when page first loads
document.addEventListener('DOMContentLoaded', function() {
    const htmxMessages = document.getElementById('htmx-messages');
    if (htmxMessages) {
        moveAndShowToasts(htmxMessages);
        htmxMessages.remove();
    }
});

// Moves notification elements into notification container and schedule it
function moveAndShowToasts(incomingMessagesDiv) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const newAlerts = incomingMessagesDiv.querySelectorAll('.alert');

    while (incomingMessagesDiv.firstChild) {
        container.appendChild(incomingMessagesDiv.firstChild);
    }

    newAlerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 1500);
    });
}

// Monitors dynamic network responses to extract and display new notifications
document.body.addEventListener('htmx:afterOnLoad', function(evt) {
    const responseText = evt.detail.xhr.responseText;
 
    if (responseText && responseText.includes('id="htmx-messages"')) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(responseText, 'text/html');
        const incomingMessages = doc.getElementById('htmx-messages');
        
        if (incomingMessages && incomingMessages.children.length > 0) {
            moveAndShowToasts(incomingMessages);
        }
    }
});

// Manage any dynamic content update
document.body.addEventListener('htmx:afterSwap', function(evt) {
    //  if modal content was loaded, initializes and launches modal overlays
    if (evt.detail.target.id === "modal-container") {
        const modalEl = document.getElementById('modal-container');
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }

    // Re-initializes interactive components inside newly swapped panels
    if (evt.detail.target.id === 'tab-content') {
        const dropdowns = evt.detail.target.querySelectorAll('[data-bs-toggle="dropdown"]');
        dropdowns.forEach(function(dropdownToggleEl) {
            bootstrap.Dropdown.getOrCreateInstance(dropdownToggleEl);
        });
        
        // Initialize contextual tooltips
        const tooltips = evt.detail.target.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(function(tooltipTriggerEl) {
            bootstrap.Tooltip.getOrCreateInstance(tooltipTriggerEl);
        });
    }
});
