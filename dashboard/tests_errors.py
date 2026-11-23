from django import forms
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import TestCase, override_settings

User = get_user_model()


class CustomErrorPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="learner", password="Pass!2345", role="LEARNER"
        )
        self.client.force_login(self.user)

    @override_settings(DEBUG=False)
    def test_unknown_lesson_slug_uses_custom_404(self):
        response = self.client.get("/lessons/does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertNotContains(response, "Traceback", status_code=404)

    @override_settings(DEBUG=False)
    def test_unknown_saved_query_id_uses_custom_404(self):
        response = self.client.get("/sandbox/saved/999999/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_error_handlers_are_registered(self):
        from sqlplayground import urls

        self.assertTrue(callable(urls.handler404))
        self.assertTrue(callable(urls.handler500))

    def test_help_text_is_escaped(self):
        class HelpTextForm(forms.Form):
            sample = forms.CharField(help_text='<img src=x onerror="alert(1)">')

        field = HelpTextForm()["sample"]
        html = render_to_string("partials/field.html", {"field": field})
        self.assertNotIn('<img src=x onerror="alert(1)">', html)
        self.assertIn("&lt;img", html)
