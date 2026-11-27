from django.conf import settings
from django.db import models
from django.db.models import Q

from .curriculum import LESSONS

LESSON_SLUGS = tuple(lesson.slug for lesson in LESSONS)
LESSON_SLUG_CHOICES = tuple((lesson.slug, lesson.title) for lesson in LESSONS)


class LessonProgress(models.Model):
    """Track one learner's attempts and completion for one lesson."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
    )
    lesson_slug = models.CharField(max_length=64, choices=LESSON_SLUG_CHOICES)
    attempts = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lesson_slug"]
        unique_together = ("user", "lesson_slug")
        constraints = [
            models.CheckConstraint(
                condition=Q(lesson_slug__in=LESSON_SLUGS),
                name="lessonprogress_slug_valid",
            )
        ]
        indexes = [
            models.Index(
                fields=["user", "completed_at"],
                name="lessonprogress_done_idx",
            )
        ]

    def __str__(self):
        return f"{self.user.username}: {self.lesson_slug}"
