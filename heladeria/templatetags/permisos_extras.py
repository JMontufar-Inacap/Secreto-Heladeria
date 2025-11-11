from django import template

register = template.Library()

@register.filter(name='tiene_grupo')
def tiene_grupo(user, nombre_grupo):
    """Verifica si el usuario pertenece a un grupo específico"""
    return user.groups.filter(name=nombre_grupo).exists()