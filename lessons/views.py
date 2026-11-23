from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import CustomUser
from dashboard.forms import SqlSubmissionForm

from .curriculum import (
    LESSONS,
    LESSONS_BY_SLUG,
    LEVELS,
    lessons_for_level,
    next_lesson,
)
from .engine import QueryError, results_match, run_query
from .models import LessonProgress


def _empty_result():
    return {
        "passed": False,
        "message": "",
        "columns": [],
        "rows": [],
        "row_count": 0,
        "truncated": False,
        "error": "",
    }


def _lesson_context(request, lesson, *, editor_sql=None, result=None, form=None):
    """Build the lesson page context for GET and invalid POST responses."""
    progress = LessonProgress.objects.filter(
        user=request.user, lesson_slug=lesson.slug
    ).first()
    if editor_sql is None:
        editor_sql = request.session.get(
            f"lesson_sql_{lesson.slug}", lesson.starter_sql
        )
    if result is None:
        result = request.session.get(f"lesson_result_{lesson.slug}")
    return {
        "lesson": lesson,
        "editor_sql": editor_sql,
        "result": result,
        "completed": bool(progress and progress.completed_at),
        "attempts": progress.attempts if progress else 0,
        "next_lesson": next_lesson(lesson),
        "form": form or SqlSubmissionForm(initial={"sql": editor_sql}),
    }


def _progress_state(user):
    completed = set(
        LessonProgress.objects.filter(
            user=user, completed_at__isnull=False
        ).values_list("lesson_slug", flat=True)
    )
    total = len(LESSONS)
    completed_count = len(completed)
    percent = round((completed_count / total) * 100) if total else 0
    current = next(
        (lesson for lesson in LESSONS if lesson.slug not in completed), None
    )
    return completed, completed_count, total, percent, current


@role_required(CustomUser.Role.LEARNER)
def lesson_index(request):
    completed, completed_count, total, percent, current = _progress_state(
        request.user
    )
    levels = []
    for level in LEVELS:
        levels.append(
            {
                "name": level,
                "lessons": [
                    {
                        "lesson": lesson,
                        "completed": lesson.slug in completed,
                        "current": current is not None
                        and lesson.slug == current.slug,
                    }
                    for lesson in lessons_for_level(level)
                ],
            }
        )

    return render(
        request,
        "lessons/index.html",
        {
            "levels": levels,
            "completed_count": completed_count,
            "total_lessons": total,
            "progress_percent": percent,
        },
    )


@role_required(CustomUser.Role.LEARNER)
def lesson_detail(request, slug):
    lesson = LESSONS_BY_SLUG.get(slug)
    if lesson is None:
        raise Http404("Lesson not found")

    return render(
        request, "lessons/detail.html", _lesson_context(request, lesson)
    )


@role_required(CustomUser.Role.LEARNER)
def lesson_check(request, slug):
    lesson = LESSONS_BY_SLUG.get(slug)
    if lesson is None:
        raise Http404("Lesson not found")
    if request.method != "POST":
        return redirect("lesson_detail", slug=slug)

    sql = (request.POST.get("sql") or "").strip()
    request.session[f"lesson_sql_{slug}"] = sql
    form = SqlSubmissionForm(request.POST)

    progress, _ = LessonProgress.objects.get_or_create(
        user=request.user, lesson_slug=slug
    )
    progress.attempts += 1
    progress.save(update_fields=["attempts", "updated_at"])

    result = _empty_result()

    if not form.is_valid():
        error = form.errors["sql"][0] if "sql" in form.errors else "Please correct the SQL below."
        result["message"] = "Your query could not run."
        result["error"] = error
        request.session[f"lesson_result_{slug}"] = result
        messages.error(request, error)
        return render(
            request,
            "lessons/detail.html",
            _lesson_context(
                request, lesson, editor_sql=sql, result=result, form=form
            ),
        )

    try:
        actual = run_query(form.cleaned_data["sql"])
        expected = run_query(lesson.reference_sql)
        passed = results_match(actual, expected, lesson.ordered)
        result.update(
            {
                "passed": passed,
                "message": lesson.success_message
                if passed
                else (
                    "Not quite yet. Compare your rows with the task and try "
                    "again."
                ),
                "columns": actual.columns,
                "rows": actual.rows,
                "row_count": len(actual.rows),
                "truncated": actual.truncated,
            }
        )
        if passed:
            messages.success(request, lesson.success_message)
            if progress.completed_at is None:
                progress.completed_at = timezone.now()
                progress.save(update_fields=["completed_at", "updated_at"])
    except QueryError as exc:
        result["message"] = "Your query could not run."
        result["error"] = str(exc)
        messages.error(request, str(exc))

    request.session[f"lesson_result_{slug}"] = result
    return redirect("lesson_detail", slug=slug)
