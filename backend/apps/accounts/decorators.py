from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles=None):
    """
    Decorator for views that checks if the logged-in user has any of the allowed roles.
    Raises PermissionDenied (403 HTTP status) if the check fails.
    """
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access this page.")
                return redirect('login')
            
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            raise PermissionDenied("You do not have permission to access this resource.")
        return _wrapped_view
    return decorator


def admin_required(view_func):
    return role_required(['ADMIN'])(view_func)


def hr_required(view_func):
    return role_required(['ADMIN', 'HR'])(view_func)


def manager_required(view_func):
    return role_required(['ADMIN', 'HR', 'MANAGER'])(view_func)
