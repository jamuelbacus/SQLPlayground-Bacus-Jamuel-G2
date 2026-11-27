from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

INACTIVE_ACCOUNT_MESSAGE = "This account is inactive. Please contact an administrator."


def _session_user_is_inactive(request):
    user = request.user
    if user.is_authenticated:
        return not user.is_active

    user_id = request.session.get("_auth_user_id")
    if not user_id:
        return False

    user_model = get_user_model()
    try:
        session_user = user_model._default_manager.get(pk=user_id)
    except user_model.DoesNotExist:
        return False
    return not session_user.is_active


def active_required(view_func):
    """End an inactive user's session before any authorization check."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if _session_user_is_inactive(request):
            logout(request)
            messages.error(request, INACTIVE_ACCOUNT_MESSAGE)
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return _wrapped


def role_required(*allowed_roles):
    """Allow a view only for active, logged-in users with an allowed role."""
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return active_required(_wrapped)

    return decorator
