from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def icon(name, size=18):
    return mark_safe(
        f'''
        <svg class="icon" width="{size}" height="{size}" aria-hidden="true">
            <use href="/static/icons/icons.svg#{name}"></use>
        </svg>
        '''
    )
