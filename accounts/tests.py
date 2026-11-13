import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()

# A valid 1x1 transparent GIF, used to test profile photo uploads.
GIF_1X1 = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
    b"\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
    b"\x00\x02\x02D\x01\x00;"
)


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

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )


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

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )
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

    def test_profile_page_requires_login(self):
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))


class ProfileTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

        self.user = User.objects.create_user(
            username="jamuel",
            email="jamuel@example.com",
            password="Str0ngPass!234",
            first_name="Jamuel",
            last_name="Bacus",
            contact_number="+639171234567",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="Str0ngPass!234",
            first_name="Other",
            last_name="Learner",
        )
        self.client.force_login(self.user)

    def test_profile_shows_only_the_logged_in_users_information(self):
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "jamuel@example.com")
        self.assertNotContains(response, "other@example.com")

    def test_profile_update_changes_only_the_logged_in_user(self):
        response = self.client.post(
            reverse("profile_edit"),
            {
                "first_name": "Jamuel",
                "last_name": "Bacus",
                "email": "new-email@example.com",
                "contact_number": "+639181234567",
            },
        )

        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.other_user.refresh_from_db()
        self.assertEqual(self.user.email, "new-email@example.com")
        self.assertEqual(self.user.contact_number, "+639181234567")
        self.assertEqual(self.other_user.email, "other@example.com")

    def test_profile_update_rejects_another_users_email(self):
        response = self.client.post(
            reverse("profile_edit"),
            {
                "first_name": "Jamuel",
                "last_name": "Bacus",
                "email": "other@example.com",
                "contact_number": "+639171234567",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "jamuel@example.com")

    def test_profile_photo_can_be_uploaded(self):
        photo = SimpleUploadedFile("avatar.gif", GIF_1X1, content_type="image/gif")

        response = self.client.post(
            reverse("profile_edit"),
            {
                "first_name": "Jamuel",
                "last_name": "Bacus",
                "email": "jamuel@example.com",
                "contact_number": "+639171234567",
                "profile_photo": photo,
            },
        )

        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_photo.name.endswith("avatar.gif"))

    def test_profile_update_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse("profile_edit"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))
