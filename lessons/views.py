from django.db import transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import CustomUser

from .curriculum import (
    LESSONS,
    LESSONS_BY_SLUG,
    LEVELS,
    lessons_for_level,
    next_lesson,
)
from .engine import QueryError, results_match, run_query
from .models import LessonProgress


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

    progress = LessonProgress.objects.filter(
        user=request.user, lesson_slug=slug
    ).first()

    return render(
        request,
        "lessons/detail.html",
        {
            "lesson": lesson,
            "editor_sql": request.session.get(
                f"lesson_sql_{slug}", lesson.starter_sql
            ),
            "result": request.session.get(f"lesson_result_{slug}"),
            "completed": bool(progress and progress.completed_at),
            "attempts": progress.attempts if progress else 0,
            "next_lesson": next_lesson(lesson),
        },
    )


@role_required(CustomUser.Role.LEARNER)
def lesson_check(request, slug):
    lesson = LESSONS_BY_SLUG.get(slug)
    if lesson is None:
        raise Http404("Lesson not found")
    if request.method != "POST":
        return redirect("lesson_detail", slug=slug)

    sql = (request.POST.get("sql") or "").strip()

    with transaction.atomic():
        progress, _ = LessonProgress.objects.get_or_create(
            user=request.user, lesson_slug=slug
        )
        LessonProgress.objects.filter(pk=progress.pk).update(
            attempts=F("attempts") + 1,
            updated_at=timezone.now(),
        )
        progress.refresh_from_db()

        result = {
            "passed": False,
            "message": "",
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "error": "",
        }

        try:
            actual = run_query(sql)
            expected = run_query(lesson.reference_sql)
            passed = results_match(actual, expected, lesson.ordered)
            result.update(
                {
                    "passed": passed,
                    "message": lesson.success_message
                    if passed
                    else (
                        "Not quite yet. Compare your rows with the task and "
                        "try again."
                    ),
                    "columns": actual.columns,
                    "rows": actual.rows,
                    "row_count": len(actual.rows),
                    "truncated": actual.truncated,
                }
            )
            if passed and progress.completed_at is None:
                LessonProgress.objects.filter(pk=progress.pk).update(
                    completed_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                progress.refresh_from_db()
        except QueryError as exc:
            result["message"] = "Your query could not run."
            result["error"] = str(exc)

    request.session[f"lesson_sql_{slug}"] = sql
    request.session[f"lesson_result_{slug}"] = result
    return redirect("lesson_detail", slug=slug)
