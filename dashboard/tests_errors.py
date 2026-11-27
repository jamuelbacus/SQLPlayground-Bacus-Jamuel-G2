from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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
