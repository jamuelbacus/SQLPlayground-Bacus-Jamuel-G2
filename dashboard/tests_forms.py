from django.contrib.auth import get_user_model
from django.test import TestCase

from dashboard.forms import SavedQueryForm

User = get_user_model()


class SavedQueryFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="learner", password="Pass!2345")

    def form(self, title="Top students", sql="SELECT * FROM students;", instance=None):
        return SavedQueryForm(
            data={"title": title, "sql": sql}, user=self.user, instance=instance
        )

    def test_valid_saved_query_form_saves(self):
        form = self.form()
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save(commit=False)
        self.assertEqual(saved.user, self.user)
        self.assertEqual(saved.title, "Top students")

    def test_blank_title_is_rejected_server_side(self):
        form = self.form(title="   ")
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_blank_sql_is_rejected_server_side(self):
        form = self.form(sql="   ")
        self.assertFalse(form.is_valid())
        self.assertIn("sql", form.errors)

    def test_duplicate_title_is_rejected_case_insensitively(self):
        self.form().save()
        duplicate = self.form(title="  top STUDENTS ")
        self.assertFalse(duplicate.is_valid())
        self.assertIn("title", duplicate.errors)

    def test_non_select_sql_is_rejected(self):
        form = self.form(sql="DELETE FROM students;")
        self.assertFalse(form.is_valid())
        self.assertIn("sql", form.errors)

    def test_multiple_statements_are_rejected(self):
        form = self.form(sql="SELECT * FROM students; SELECT * FROM courses;")
        self.assertFalse(form.is_valid())
        self.assertIn("sql", form.errors)

    def test_read_only_cte_is_accepted(self):
        form = self.form(sql="WITH top AS (SELECT * FROM students) SELECT * FROM top;")
        self.assertTrue(form.is_valid(), form.errors)

    def test_saved_query_title_html_is_escaped(self):
        form = self.form(title="<script>alert(1)</script>")
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save(commit=False)
        saved.user = self.user
        saved.save()
        self.client.force_login(self.user)
        response = self.client.get(f"/sandbox/saved/{saved.pk}/")
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
