document.body.addEventListener('htmx:afterOnLoad', function(evt) {
    if (evt.detail.target.id === 'tab-content') {
        const tabs = document.querySelectorAll('#projectTabs .nav-link');
        tabs.forEach(link => link.classList.remove('active'));
        const requestPath = evt.detail.requestConfig.path;
        const activeTab = document.querySelector(`#projectTabs .nav-link[hx-get="${requestPath}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }
    }
});