from django import template

register = template.Library()

@register.filter(name='status_css')
def status_css(status: str) -> str:
    mapping = {
        'converted': 'bg-success-subtle text-success border-success-subtle',
        'reviewed': 'bg-warning-subtle text-warning border-warning-subtle',
        'declined': 'bg-danger-subtle text-danger border-danger-subtle',
    }
    return mapping.get(status, 'bg-info-subtle text-info border-info-subtle')

@register.filter(name='status_icon')
def status_icon(status: str) -> str:
    mapping = {
        'converted': 'bi-check-circle-fill',
        'reviewed': 'bi-eye-fill',
        'declined': 'bi-dash-circle-fill',
    }
    return mapping.get(status, 'bi-hourglass-split')
