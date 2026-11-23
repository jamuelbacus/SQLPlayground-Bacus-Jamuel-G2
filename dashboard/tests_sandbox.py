from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import QueryHistory, SavedQuery

User = get_user_model()


class SandboxAccessTests(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            username="learner1",
            email="learner1@example.com",
            password="Str0ngPass!234",
        )
        self.administrator = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="Str0ngPass!234",
            role=User.Role.ADMINISTRATOR,
        )

    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse("sandbox"))

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('sandbox')}"
        )

    def test_administrator_cannot_open_sandbox(self):
        self.client.force_login(self.administrator)

        self.assertEqual(self.client.get(reverse("sandbox")).status_code, 403)

    def test_learner_opens_sandbox_with_schema(self):
        self.client.force_login(self.learner)

        response = self.client.get(reverse("sandbox"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/sandbox.html")
        self.assertEqual(
            [table["name"] for table in response.context["database_schema"]],
            ["students", "courses", "enrollments"],
        )

    def test_old_learning_url_redirects_permanently(self):
        self.client.force_login(self.learner)

        response = self.client.get("/dashboard/learning/")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, reverse("sandbox"))


class SandboxExecutionTests(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            username="learner1",
            email="learner1@example.com",
            password="Str0ngPass!234",
        )
        self.client.force_login(self.learner)

    def test_successful_query_returns_rows_and_records_history(self):
        response = self.client.post(
            reverse("sandbox_execute"),
            {"sql": "SELECT first_name, last_name FROM students;"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        result = response.context["last_result"]
        self.assertTrue(result["success"])
        self.assertEqual(result["row_count"], 6)
        self.assertEqual(result["columns"], ["first_name", "last_name"])

        history = QueryHistory.objects.get(user=self.learner)
        self.assertEqual(history.status, "success")
        self.assertEqual(history.row_count, 6)

    def test_invalid_query_records_an_error(self):
        response = self.client.post(
            reverse("sandbox_execute"),
            {"sql": "SELEC first_name FROM students;"},
            follow=True,
        )

        result = response.context["last_result"]
        self.assertFalse(result["success"])
        self.assertIn("Only SELECT queries", result["error"])

        history = QueryHistory.objects.get(user=self.learner)
        self.assertEqual(history.status, "error")
        self.assertIn("Only SELECT queries", history.error_message)

    def test_application_tables_are_not_reachable(self):
        response = self.client.post(
            reverse("sandbox_execute"),
            {"sql": "SELECT * FROM accounts_customuser;"},
            follow=True,
        )

        result = response.context["last_result"]
        self.assertFalse(result["success"])
        self.assertIn("no such table", result["error"])

    def test_get_execute_redirects_without_running(self):
        response = self.client.get(reverse("sandbox_execute"))

        self.assertRedirects(response, reverse("sandbox"))
        self.assertFalse(QueryHistory.objects.exists())

    def test_last_query_is_restored_on_the_next_visit(self):
        self.client.post(
            reverse("sandbox_execute"),
            {"sql": "SELECT course_name FROM courses;"},
        )

        response = self.client.get(reverse("sandbox"))

        self.assertContains(response, "SELECT course_name FROM courses;")

    def test_sql_submission_over_limit_is_rejected(self):
        from dashboard.forms import SqlSubmissionForm

        form = SqlSubmissionForm(data={"sql": "SELECT " + "x" * 6000})

        self.assertFalse(form.is_valid())
        self.assertIn("sql", form.errors)


class SavedQueryTests(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            username="learner1",
            email="learner1@example.com",
            password="Str0ngPass!234",
        )
        self.other_learner = User.objects.create_user(
            username="learner2",
            email="learner2@example.com",
            password="Str0ngPass!234",
        )
        self.client.force_login(self.learner)
        self.saved_query = SavedQuery.objects.create(
            user=self.learner,
            title="All students",
            sql="SELECT * FROM students;",
        )

    def test_saved_query_list_is_available_from_the_sandbox(self):
        response = self.client.get(reverse("saved_query_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "All students")
        self.assertContains(response, reverse("sandbox"))

    def test_learner_can_create_a_saved_query(self):
        response = self.client.post(
            reverse("saved_query_create"),
            {"title": "Courses", "sql": "SELECT * FROM courses;"},
        )

        created = SavedQuery.objects.get(user=self.learner, title="Courses")
        self.assertRedirects(
            response, reverse("saved_query_detail", args=[created.pk])
        )

    def test_learner_cannot_open_another_learners_saved_query(self):
        self.client.force_login(self.other_learner)

        response = self.client.get(
            reverse("saved_query_detail", args=[self.saved_query.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_saved_query_delete_removes_the_query(self):
        response = self.client.post(
            reverse("saved_query_delete", args=[self.saved_query.pk])
        )

        self.assertRedirects(response, reverse("saved_query_list"))
        self.assertFalse(SavedQuery.objects.exists())
