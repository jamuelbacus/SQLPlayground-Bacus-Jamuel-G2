from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse

from lessons.engine import QueryError
from sqlplayground.views import custom_404, custom_500

User = get_user_model()


class CustomErrorHandlingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="learner",
            email="learner@example.com",
            password="Str0ngPass!234",
        )
        self.client.force_login(self.user)
        self.client.raise_request_exception = False

    def test_error_handlers_are_registered(self):
        from sqlplayground import urls

        self.assertIs(urls.handler404, custom_404)
        self.assertIs(urls.handler500, custom_500)

    def test_missing_saved_query_uses_custom_404(self):
        response = self.client.get(reverse("saved_query_detail", args=[999999]))

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertNotContains(response, "Traceback", status_code=404)

    def test_unknown_lesson_slug_uses_custom_404(self):
        response = self.client.get(reverse("lesson_detail", args=["does-not-exist"]))

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertNotContains(response, "Traceback", status_code=404)

    @patch(
        "dashboard.views.LessonProgress.objects.filter",
        side_effect=DatabaseError(
            "connection lost dsn=postgres://user:supersecret@host/db"
        ),
    )
    def test_database_error_renders_custom_500_without_sensitive_text(self, _filter):
        with patch("django.utils.log.request_logger.error"):
            response = self.client.get(reverse("learner_dashboard"))

        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, "500.html")
        for sensitive in (
            "Traceback",
            "DatabaseError",
            "supersecret",
            "dsn=",
            "postgres://",
        ):
            with self.subTest(sensitive=sensitive):
                self.assertNotContains(response, sensitive, status_code=500)

    @patch("dashboard.views.run_query", side_effect=QueryError("Only SELECT is allowed."))
    def test_practice_sql_error_keeps_existing_handling(self, _run_query):
        response = self.client.post(
            reverse("sandbox_execute"), {"sql": "SELECT * FROM students;"}
        )

        self.assertRedirects(response, reverse("sandbox"))
        followup = self.client.get(reverse("sandbox"))
        self.assertEqual(followup.status_code, 200)
        self.assertTemplateNotUsed(followup, "500.html")
        self.assertContains(followup, "Only SELECT is allowed.")
