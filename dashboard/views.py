from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.decorators import role_required
from accounts.models import CustomUser


@login_required
def dashboard_redirect(request):
    """Send each user to the dashboard that belongs to their role."""
    if request.user.is_administrator:
        return redirect("administrator_dashboard")
    return redirect("learner_dashboard")


@role_required(CustomUser.Role.LEARNER)
def learner_dashboard(request):
    return render(request, "dashboard/learner_dashboard.html")


@role_required(CustomUser.Role.ADMINISTRATOR)
def administrator_dashboard(request):
    users = CustomUser.objects.order_by("-date_joined")
    context = {
        "total_users": users.count(),
        "total_learners": users.filter(role=CustomUser.Role.LEARNER).count(),
        "total_administrators": users.filter(role=CustomUser.Role.ADMINISTRATOR).count(),
        "recent_users": users[:5],
    }
    return render(request, "dashboard/administrator_dashboard.html", context)
