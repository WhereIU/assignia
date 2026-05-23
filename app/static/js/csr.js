document.body.addEventListener('htmx:afterSettle', function(evt) {
    var htmxMessages = document.getElementById('htmx-messages');
    if (htmxMessages) {
        var toastContainer = document.getElementById('toast-container');
        while (htmxMessages.firstChild) {
            toastContainer.appendChild(htmxMessages.firstChild);
        }
        htmxMessages.remove();
        setTimeout(function() {
            var toasts = toastContainer.querySelectorAll('.toast');
            toasts.forEach(function(toast) {
                var bsToast = bootstrap.Toast.getInstance(toast);
                if (bsToast) {
                    bsToast.hide();
                } else {
                    toast.remove();
                }
            });
        }, 2000);
    }
});

document.addEventListener('DOMContentLoaded', function moveToasts() {
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

