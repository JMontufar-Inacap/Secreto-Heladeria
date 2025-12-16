from django.core.exceptions import PermissionDenied

def grupo_requerido(*grupos):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.groups.filter(name__in=grupos).exists():
                    return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator
