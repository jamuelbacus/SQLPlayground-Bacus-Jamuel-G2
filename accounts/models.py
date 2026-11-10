from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class CustomUser(AbstractUser):
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

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMINISTRATOR
        super().save(*args, **kwargs)

    @property
    def is_learner(self):
        return self.role == self.Role.LEARNER

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMINISTRATOR

    def __str__(self):
        return self.username