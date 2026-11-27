from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class QueryHistory(models.Model):
    """Track executed SQL statements for each learner."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="query_history",
    )
    sql = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=(("success", "Success"), ("error", "Error")),
        default="success",
    )
    row_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-executed_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=("success", "error")),
                name="queryhistory_status_valid",
            )
        ]
        indexes = [
            models.Index(
                fields=["user", "-executed_at"],
                name="queryhistory_user_recent_idx",
            )
        ]

    def __str__(self):
        return f"{self.user.username}: {self.sql[:40]}"


class SavedQuery(models.Model):
    """Store a learner's saved SQL query."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_queries",
    )
    title = models.CharField(max_length=200)
    sql = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                "user",
                Lower("title"),
                name="savedquery_user_title_ci_uniq",
            )
        ]
        indexes = [
            models.Index(
                fields=["user", "-updated_at", "-created_at"],
                name="savedquery_user_recent_idx",
            )
        ]

    def __str__(self):
        return self.title
