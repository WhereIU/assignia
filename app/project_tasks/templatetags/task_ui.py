from django import template

register = template.Library()

@register.filter(name='task_status_css')
def task_status_css(status: str) -> str:
    mapping = {
        'done': 'bg-success-subtle text-success border-success-subtle',
        'in_progress': 'bg-primary-subtle text-primary border-primary-subtle',
        'pending': 'bg-warning-subtle text-warning border-warning-subtle',
        'cancelled': 'bg-secondary-subtle text-secondary border-secondary-subtle',
    }
    return mapping.get(status, 'bg-info-subtle text-info border-info-subtle')

@register.filter(name='task_status_icon')
def task_status_icon(status: str) -> str:
    mapping = {
        'done': 'bi-check-all',
        'in_progress': 'bi-gear-fill spin',
    }
    return mapping.get(status, 'bi-circle')

@register.filter(name='priority_icon_color')
def priority_icon_color(priority: int | str) -> str:
    try:
        p = int(priority)
    except (ValueError, TypeError):
        return 'text-muted'
        
    if p >= 4:
        return 'text-danger'
    if p == 3:
        return 'text-warning'
    return 'text-success'

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": f"{field.field.widget.attrs.get('class', '')} {css_class}"})