import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.decorators import INACTIVE_ACCOUNT_MESSAGE
from dashboard.models import QueryHistory, SavedQuery
from lessons.models import LessonProgress

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


    def test_login_accepts_email_address(self):
        response = self.client.post(
            self.login_url,
            {"username": "learner1@example.com", "password": "Str0ngPass!234"},
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_accepts_email_case_insensitively(self):
        response = self.client.post(
            self.login_url,
            {"username": "Learner1@Example.com", "password": "Str0ngPass!234"},
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_prefers_exact_username_over_email_match(self):
        username_owner = User.objects.create_user(
            username="shared@example.com",
            email="username-owner@example.com",
            password="Str0ngPass!234",
        )
        User.objects.create_user(
            username="email-owner",
            email="shared@example.com",
            password="DifferentPass!234",
        )

        response = self.client.post(
            self.login_url,
            {"username": "shared@example.com", "password": "Str0ngPass!234"},
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )
        self.assertEqual(int(self.client.session["_auth_user_id"]), username_owner.pk)

    def test_login_rejects_ambiguous_email_match(self):
        User.objects.create_user(
            username="case-a",
            email="Case@example.com",
            password="Str0ngPass!234",
        )
        User.objects.create_user(
            username="case-b",
            email="case@example.com",
            password="DifferentPass!234",
        )

        response = self.client.post(
            self.login_url,
            {"username": "case@example.com", "password": "Str0ngPass!234"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Invalid username or password")

    def test_remember_me_unchecked_expires_at_browser_close(self):
        self.client.post(
            self.login_url,
            {"username": "learner1", "password": "Str0ngPass!234"},
        )

        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_remember_me_checked_expires_in_30_days(self):
        self.client.post(
            self.login_url,
            {
                "username": "learner1",
                "password": "Str0ngPass!234",
                "remember_me": "on",
            },
        )

        self.assertGreater(
            self.client.session.get_expiry_age(),
            60 * 60 * 24 * 29,
        )

    def test_login_form_uses_username_or_email_label(self):
        response = self.client.get(self.login_url)

        self.assertContains(response, "Username or email")


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
            },
        )

        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.other_user.refresh_from_db()
        self.assertEqual(self.user.email, "new-email@example.com")
        self.assertEqual(self.other_user.email, "other@example.com")

    def test_profile_update_rejects_another_users_email(self):
        response = self.client.post(
            reverse("profile_edit"),
            {
                "first_name": "Jamuel",
                "last_name": "Bacus",
                "email": "other@example.com",
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


class InactiveSessionAccessTests(TestCase):
    def setUp(self):
        self.login_url = reverse("login")
        self.learner = User.objects.create_user(
            username="inactive-learner",
            email="inactive-learner@example.com",
            password="Str0ngPass!234",
        )
        self.administrator = User.objects.create_user(
            username="inactive-admin",
            email="inactive-admin@example.com",
            password="Str0ngPass!234",
            role=User.Role.ADMINISTRATOR,
        )
        self.target = User.objects.create_user(
            username="target",
            email="target@example.com",
            password="Str0ngPass!234",
        )
        self.saved_query = SavedQuery.objects.create(
            user=self.learner,
            title="All students",
            sql="SELECT * FROM students",
        )

    def assert_inactive_redirect(self, url, user):
        self.client.force_login(user)
        User.objects.filter(pk=user.pk).update(is_active=False)

        response = self.client.get(url, follow=True)

        self.assertEqual(response.redirect_chain[0][0], self.login_url)
        self.assertContains(response, INACTIVE_ACCOUNT_MESSAGE)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_deactivated_learner_is_redirected_from_role_protected_pages(self):
        for url in (
            reverse("learner_dashboard"),
            reverse("sandbox"),
            reverse("saved_query_list"),
            reverse("saved_query_create"),
            reverse("saved_query_detail", args=[self.saved_query.pk]),
            reverse("saved_query_edit", args=[self.saved_query.pk]),
            reverse("saved_query_delete", args=[self.saved_query.pk]),
            reverse("lesson_index"),
            reverse("lesson_detail", args=["select-columns"]),
        ):
            with self.subTest(url=url):
                self.assert_inactive_redirect(url, self.learner)

    def test_deactivated_administrator_is_redirected_from_user_management(self):
        for url in (
            reverse("administrator_dashboard"),
            reverse("manage_users"),
            reverse("user_create"),
            reverse("user_edit", args=[self.target.pk]),
            reverse("user_password", args=[self.target.pk]),
            reverse("user_delete", args=[self.target.pk]),
        ):
            with self.subTest(url=url):
                self.assert_inactive_redirect(url, self.administrator)

    def test_active_users_keep_their_existing_access(self):
        self.client.force_login(self.learner)
        self.assertEqual(self.client.get(reverse("sandbox")).status_code, 200)

        self.client.force_login(self.administrator)
        self.assertEqual(self.client.get(reverse("manage_users")).status_code, 200)
