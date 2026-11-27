from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import CustomUser
from lessons.curriculum import LESSONS
from lessons.engine import QueryError, run_query, schema_tables
from lessons.models import LessonProgress

from .forms import AdminUserCreateForm, AdminUserEditForm
from .models import QueryHistory, SavedQuery

DEFAULT_SQL = "SELECT * FROM students ORDER BY student_id;"


@login_required
def dashboard_redirect(request):
    """Send each user to the dashboard that belongs to their role."""
    if request.user.is_administrator:
        return redirect("administrator_dashboard")
    return redirect("learner_dashboard")


@role_required(CustomUser.Role.LEARNER)
def learner_dashboard(request):
    completed = set(
        LessonProgress.objects.filter(
            user=request.user, completed_at__isnull=False
        ).values_list("lesson_slug", flat=True)
    )
    total_lessons = len(LESSONS)
    completed_count = len(completed)
    progress_percent = (
        round((completed_count / total_lessons) * 100) if total_lessons else 0
    )
    current_lesson = next(
        (lesson for lesson in LESSONS if lesson.slug not in completed), None
    )
    context = {
        "saved_query_count": request.user.saved_queries.count(),
        "query_history_count": request.user.query_history.count(),
        "completed_lesson_count": completed_count,
        "total_lessons": total_lessons,
        "progress_percent": progress_percent,
        "current_lesson": current_lesson,
        "sample_database_count": 1,
    }
    return render(request, "dashboard/learner_dashboard.html", context)


@role_required(CustomUser.Role.LEARNER)
def sandbox(request):
    """Free SQL practice against the isolated sample database."""
    default_sql = (
        request.GET.get("sql")
        or request.session.get("sandbox_sql")
        or DEFAULT_SQL
    )
    last_result = request.session.get(
        "sandbox_result",
        {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "error": "",
            "message": "",
        },
    )
    context = {
        "database_schema": schema_tables(),
        "query_history": request.user.query_history.select_related("user").all()[:10],
        "saved_queries": request.user.saved_queries.select_related("user").all()[:10],
        "default_sql": default_sql,
        "last_result": last_result,
    }
    return render(request, "dashboard/sandbox.html", context)


@role_required(CustomUser.Role.LEARNER)
def sandbox_execute(request):
    """Run one SELECT in the sandbox and keep the result for the next page."""
    if request.method != "POST":
        return redirect("sandbox")

    sql = (request.POST.get("sql") or "").strip()
    request.session["sandbox_sql"] = sql

    try:
        result = run_query(sql)
    except QueryError as exc:
        QueryHistory.objects.create(
            user=request.user,
            sql=sql,
            status="error",
            error_message=str(exc),
        )
        request.session["sandbox_result"] = {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "error": str(exc),
            "message": "Your query could not run.",
        }
        return redirect("sandbox")

    QueryHistory.objects.create(
        user=request.user,
        sql=sql,
        status="success",
        row_count=len(result.rows),
    )
    request.session["sandbox_result"] = {
        "success": True,
        "columns": result.columns,
        "rows": result.rows,
        "row_count": len(result.rows),
        "truncated": result.truncated,
        "error": "",
        "message": "Query executed successfully.",
    }
    return redirect("sandbox")


@role_required(CustomUser.Role.LEARNER)
def saved_query_list(request):
    return render(
        request,
        "dashboard/saved_query_list.html",
        {
            "saved_queries": request.user.saved_queries.select_related("user").all()
        },
    )


@role_required(CustomUser.Role.LEARNER)
def saved_query_create(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        sql = (request.POST.get("sql") or "").strip()
        if not title:
            messages.error(request, "A title is required for saving a query.")
            return redirect("saved_query_list")
        saved_query = SavedQuery.objects.create(user=request.user, title=title, sql=sql)
        messages.success(request, f"Saved query '{saved_query.title}' was created.")
        return redirect("saved_query_detail", pk=saved_query.pk)

    return render(
        request,
        "dashboard/saved_query_form.html",
        {"page_title": "Save Query", "saved_query": None},
    )


@role_required(CustomUser.Role.LEARNER)
def saved_query_detail(request, pk):
    saved_query = get_object_or_404(SavedQuery, pk=pk, user=request.user)
    return render(request, "dashboard/saved_query_detail.html", {"saved_query": saved_query})


@role_required(CustomUser.Role.LEARNER)
def saved_query_edit(request, pk):
    saved_query = get_object_or_404(SavedQuery, pk=pk, user=request.user)
    if request.method == "POST":
        saved_query.title = (request.POST.get("title") or "").strip()
        saved_query.sql = (request.POST.get("sql") or "").strip()
        if not saved_query.title:
            messages.error(request, "A title is required for saving a query.")
        else:
            saved_query.save()
            messages.success(request, f"Saved query '{saved_query.title}' was updated.")
            return redirect("saved_query_detail", pk=saved_query.pk)

    return render(
        request,
        "dashboard/saved_query_form.html",
        {"page_title": "Edit Query", "saved_query": saved_query},
    )


@role_required(CustomUser.Role.LEARNER)
def saved_query_delete(request, pk):
    saved_query = get_object_or_404(SavedQuery, pk=pk, user=request.user)
    if request.method == "POST":
        title = saved_query.title
        saved_query.delete()
        messages.success(request, f"Saved query '{title}' was deleted.")
        return redirect("saved_query_list")
    return render(
        request,
        "dashboard/saved_query_detail.html",
        {"saved_query": saved_query, "confirm_delete": True},
    )


@role_required(CustomUser.Role.ADMINISTRATOR)
def administrator_dashboard(request):
    counts = CustomUser.objects.aggregate(
        total_learners=Count("id", filter=Q(role=CustomUser.Role.LEARNER)),
        total_administrators=Count(
            "id", filter=Q(role=CustomUser.Role.ADMINISTRATOR)
        ),
    )
    context = {
        "total_learners": counts["total_learners"],
        "total_administrators": counts["total_administrators"],
        "recent_users": CustomUser.objects.order_by("-date_joined")[:5],
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
