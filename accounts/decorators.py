from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """Allow a view only for logged-in users whose role is in allowed_roles.

    Anonymous users are sent to the login page by login_required. Authenticated
    users with the wrong role receive HTTP 403 Forbidden, so they cannot open
    another role's dashboard just by typing its URL.
    """

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
