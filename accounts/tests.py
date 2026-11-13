from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()



class SignUpTests(TestCase):
    def setUp(self):
        self.url = reverse("signup")
        self.valid_data = {
            "first_name": "Jamuel",
            "last_name": "Bacus",
            "username": "jamuel",
            "email": "jamuel@example.com",
            "contact_number": "+639171234567",
            "password1": "Str0ngPass!234",
            "password2": "Str0ngPass!234",
        }

    def test_signup_page_loads(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/signup.html")

    def test_valid_signup_creates_learner_with_hashed_password(self):
        response = self.client.post(self.url, self.valid_data)

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="jamuel")
        self.assertEqual(user.role, User.Role.LEARNER)
        self.assertTrue(user.check_password("Str0ngPass!234"))
        self.assertNotEqual(user.password, "Str0ngPass!234")
        self.assertFalse(self.client.session.get("_auth_user_id"))

    def test_password_confirmation_must_match(self):
        data = {**self.valid_data, "password2": "DifferentPass!234"}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("password2", response.context["form"].errors)
        self.assertFalse(User.objects.filter(username="jamuel").exists())

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            username="existing",
            email="jamuel@example.com",
            password="Str0ngPass!234",
        )
        data = {**self.valid_data, "username": "another"}

        response = self.client.post(self.url, data)

        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="jamuel",
            email="other@example.com",
            password="Str0ngPass!234",
        )

        response = self.client.post(self.url, self.valid_data)

        self.assertIn("username", response.context["form"].errors)

    def test_invalid_email_format_is_rejected(self):
        data = {**self.valid_data, "email": "not-an-email"}

        response = self.client.post(self.url, data)

        self.assertIn("email", response.context["form"].errors)

    def test_required_fields_are_enforced(self):
        response = self.client.post(self.url, {})

        form = response.context["form"]
        for field in ("first_name", "last_name", "username", "email", "password1", "password2"):
            self.assertIn(field, form.errors)

    def test_logged_in_user_is_redirected_away_from_signup(self):
        user = User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="Str0ngPass!234",
        )
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("home"))


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="learner1",
            email="learner1@example.com",
            password="Str0ngPass!234",
        )
        self.login_url = reverse("login")

    def test_login_page_loads(self):
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_valid_credentials_log_the_user_in(self):
        response = self.client.post(
            self.login_url,
            {"username": "learner1", "password": "Str0ngPass!234"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_invalid_credentials_show_an_error_message(self):
        response = self.client.post(
            self.login_url,
            {"username": "learner1", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_logout_ends_the_session(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
