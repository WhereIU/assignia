// Adds shortcut for comments
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const target = e.target;
        if (target.tagName === 'TEXTAREA' && target.name === 'text') {
            target.form.requestSubmit();
        }
    }
});
