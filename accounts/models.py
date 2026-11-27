from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q


class CustomUser(AbstractUser):
    """Application user with a role, contact number, and profile photo."""

    class Role(models.TextChoices):
        LEARNER = "LEARNER", "Learner"
        ADMINISTRATOR = "ADMINISTRATOR", "Administrator"

    email = models.EmailField("email address", unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.LEARNER,
    )

    contact_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?[0-9]{7,15}$",
                message="Enter a valid contact number (7-15 digits, optional leading +).",
            )
        ],
    )

    profile_photo = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
        null=True,
    )

    class Meta(AbstractUser.Meta):
        constraints = [
            models.CheckConstraint(
                condition=Q(role__in=("LEARNER", "ADMINISTRATOR")),
                name="customuser_role_valid",
            )
        ]
        indexes = [
            models.Index(
                fields=["role", "is_active"],
                name="customuser_role_active_idx",
            )
        ]

    def save(self, *args, **kwargs):
        # Superusers are always administrators, even if created through
        # createsuperuser without choosing a role.
        if self.is_superuser:
            self.role = self.Role.ADMINISTRATOR
        super().save(*args, **kwargs)

    @property
    def is_learner(self):
        return self.role == self.Role.LEARNER

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMINISTRATOR

    @property
    def display_name(self):
        """Return the full name when available, otherwise the username."""
        return self.get_full_name() or self.username

    def __str__(self):
        return self.username
