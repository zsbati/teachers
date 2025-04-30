from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='euro_format')
def euro_format(value):
    """Format a number as currency with euros"""
    if value is None:
        return ''
    return mark_safe(f"{value:,.2f} €")
