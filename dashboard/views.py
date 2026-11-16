from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import CustomUser

from .forms import AdminUserCreateForm, AdminUserEditForm


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
        "total_learners": users.filter(role=CustomUser.Role.LEARNER).count(),
        "total_administrators": users.filter(role=CustomUser.Role.ADMINISTRATOR).count(),
        "recent_users": users[:5],
    }
    return render(request, "dashboard/administrator_dashboard.html", context)


@role_required(CustomUser.Role.ADMINISTRATOR)
def manage_users(request):
    """List, search, and filter every account."""
    users = CustomUser.objects.order_by("-date_joined")
    query = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    status = request.GET.get("status", "").strip()

    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
    if role in CustomUser.Role.values:
        users = users.filter(role=role)
    if status == "active":
        users = users.filter(is_active=True)
    elif status == "inactive":
        users = users.filter(is_active=False)

    paginator = Paginator(users, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)

    context = {
        "page_obj": page_obj,
        "total_count": paginator.count,
        "query": query,
        "role": role,
        "status": status,
        "role_choices": CustomUser.Role.choices,
        "status_choices": (("active", "Active"), ("inactive", "Inactive")),
        "querystring": params.urlencode(),
    }
    return render(request, "dashboard/manage_users.html", context)


@role_required(CustomUser.Role.ADMINISTRATOR)
def user_create(request):
    """Create a learner or administrator account."""
    if request.method == "POST":
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            account = form.save()
            messages.success(request, f"Account {account.username} was created.")
            return redirect("manage_users")
        messages.error(request, "Please correct the errors below.")
    else:
        form = AdminUserCreateForm()

    return render(
        request,
        "dashboard/user_form.html",
        {"form": form, "page_title": "Create User", "target": None},
    )


def _is_last_active_administrator(account):
    if not account.is_administrator or not account.is_active:
        return False
    return not (
        CustomUser.objects.filter(
            role=CustomUser.Role.ADMINISTRATOR, is_active=True
        )
        .exclude(pk=account.pk)
        .exists()
    )


@role_required(CustomUser.Role.ADMINISTRATOR)
def user_edit(request, pk):
    """Update an account's details, role, and active status."""
    target = get_object_or_404(CustomUser, pk=pk)
    editing_self = target.pk == request.user.pk

    if request.method == "POST":
        form = AdminUserEditForm(request.POST, instance=target)
        if editing_self or target.is_superuser:
            form.fields["role"].disabled = True
        if editing_self:
            form.fields["is_active"].disabled = True

        if form.is_valid():
            new_role = form.cleaned_data["role"]
            new_active = form.cleaned_data["is_active"]
            removes_last_admin = (
                target.is_administrator
                and (new_role != CustomUser.Role.ADMINISTRATOR or not new_active)
                and _is_last_active_administrator(target)
            )
            if removes_last_admin:
                form.add_error(
                    None, "At least one active administrator must remain."
                )
            else:
                form.save()
                messages.success(request, f"Account {target.username} was updated.")
                return redirect("manage_users")
        messages.error(request, "Please correct the errors below.")
    else:
        form = AdminUserEditForm(instance=target)
        if editing_self or target.is_superuser:
            form.fields["role"].disabled = True
        if editing_self:
            form.fields["is_active"].disabled = True

    return render(
        request,
        "dashboard/user_form.html",
        {"form": form, "page_title": "Edit User", "target": target},
    )


@role_required(CustomUser.Role.ADMINISTRATOR)
def user_password(request, pk):
    """Change an account's password without the Django admin site."""
    target = get_object_or_404(CustomUser, pk=pk)

    if request.method == "POST":
        form = AdminPasswordChangeForm(target, request.POST)
        if form.is_valid():
            form.save()
            if target.pk == request.user.pk:
                update_session_auth_hash(request, target)
            messages.success(request, f"Password for {target.username} was changed.")
            return redirect("user_edit", pk=target.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = AdminPasswordChangeForm(target)

    return render(
        request,
        "dashboard/user_password.html",
        {"form": form, "page_title": "Change Password", "target": target},
    )


@role_required(CustomUser.Role.ADMINISTRATOR)
def user_delete(request, pk):
    """Delete an account after a confirmation step."""
    target = get_object_or_404(CustomUser, pk=pk)

    if target.pk == request.user.pk:
        messages.error(request, "You cannot delete your own account.")
        return redirect("manage_users")

    if request.method == "POST":
        if _is_last_active_administrator(target):
            messages.error(
                request, "At least one active administrator must remain."
            )
            return redirect("user_delete", pk=target.pk)
        username = target.username
        target.delete()
        messages.success(request, f"Account {username} was deleted.")
        return redirect("manage_users")

    return render(
        request,
        "dashboard/user_confirm_delete.html",
        {"target": target, "page_title": "Delete User"},
    )
