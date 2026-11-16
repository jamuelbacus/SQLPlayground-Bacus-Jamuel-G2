from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="QueryHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sql", models.TextField()),
                ("status", models.CharField(choices=[("success", "Success"), ("error", "Error")], default="success", max_length=20)),
                ("row_count", models.IntegerField(default=0)),
                ("error_message", models.TextField(blank=True, default="")),
                ("executed_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="query_history", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-executed_at"],
            },
        ),
        migrations.CreateModel(
            name="SavedQuery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("sql", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_queries", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-updated_at", "-created_at"],
            },
        ),
    ]
