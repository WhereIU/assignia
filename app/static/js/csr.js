document.addEventListener('DOMContentLoaded', function() {
    var htmxMessages = document.getElementById('htmx-messages');
    if (htmxMessages) {
        var container = document.getElementById('toast-container');
        while (htmxMessages.firstChild) {
            container.appendChild(htmxMessages.firstChild);
        }
        htmxMessages.remove();
        var alerts = container.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 2000);
        });
    }
});

document.body.addEventListener('htmx:afterSettle', function() {
    var htmxMessages = document.getElementById('htmx-messages');
    if (htmxMessages) {
        var container = document.getElementById('toast-container');
        while (htmxMessages.firstChild) {
            container.appendChild(htmxMessages.firstChild);
        }
        htmxMessages.remove();
        var alerts = container.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 2000);
        });
    }
});