from django.conf import settings
from django.db import models


class LessonProgress(models.Model):
    """Track one learner's attempts and completion for one lesson."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
    )
    lesson_slug = models.CharField(max_length=64)
    attempts = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lesson_slug"]
        unique_together = ("user", "lesson_slug")

    def __str__(self):
        return f"{self.user.username}: {self.lesson_slug}"
