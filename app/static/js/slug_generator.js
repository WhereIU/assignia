// Generate slug for project name
document.addEventListener('DOMContentLoaded', function() {
    const nameInput = document.getElementById('id_name');
    const slugInput = document.getElementById('id_slug');
    const slugPreview = document.getElementById('slug-preview');
    
    if (!nameInput || !slugInput || !slugPreview) return;

    let userTypedSlug = false;

    function slugify(text) {
        return text.trim()
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_]+/g, '-')
            .replace(/-+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    function updatePreview(slug) {
        if (slug === undefined || slug === '') {
            slug = slugify(nameInput.value) || 'my-new-project';
        }
        slugPreview.textContent = slug;
    }

    if (slugInput.value.trim()) {
        userTypedSlug = true;
        updatePreview(slugInput.value);
    } else if (nameInput.value.trim()) {
        updatePreview('');
    }

    nameInput.addEventListener('input', function() {
        if (!userTypedSlug) {
            updatePreview('');
        }
    });

    slugInput.addEventListener('input', function() {
        userTypedSlug = true;
        updatePreview(this.value);
    });

    slugInput.addEventListener('change', function() {
        if (!this.value.trim()) {
            userTypedSlug = false;
            updatePreview('');
        }
    });
});