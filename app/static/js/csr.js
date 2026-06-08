document.addEventListener('DOMContentLoaded', function() {
    const htmxMessages = document.getElementById('htmx-messages');
    if (htmxMessages) {
        moveAndShowToasts(htmxMessages);
        htmxMessages.remove();
    }
});

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

document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === "modal-container") {
        const modalEl = document.getElementById('modal-container');
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
});