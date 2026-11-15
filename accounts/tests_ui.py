from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class PublicChromeTests(TestCase):
    def test_home_contains_public_navigation(self):
        response = self.client.get(reverse("home"))

        for label in ("Home", "Features", "About", "FAQ"):
            self.assertContains(response, label)
        self.assertContains(response, "#features")

    def test_home_uses_light_and_dark_logo_assets(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "img/logo-light.svg")
        self.assertContains(response, "img/logo-dark.svg")

    def test_guest_header_has_login_and_create_account(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "Log in")
        self.assertContains(response, "Create account")

    def test_authenticated_header_has_account_actions(self):
        user = User.objects.create_user(
            username="learner",
            email="learner@example.com",
            password="Str0ngPass!234",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Profile")
        self.assertContains(response, "Log out")

    def test_theme_toggle_and_site_script_are_present(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "data-theme-toggle")
        self.assertContains(response, "js/site.js")

    def test_layout_has_skip_link_and_mobile_menu(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "Skip to content")
        self.assertContains(response, 'id="main-content"')
        self.assertContains(response, "data-menu-toggle")
        self.assertContains(response, "data-mobile-menu")

    def test_home_has_full_landing_sections(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "Master SQL one query at a time.")
        self.assertContains(response, "Start Practicing")
        self.assertContains(response, 'id="features"')
        self.assertContains(response, 'id="about"')
        self.assertContains(response, 'id="faq"')
        self.assertContains(response, "Ready to write your first query?")

    def test_product_preview_runs_on_click(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "Preview of the SQL Playground editor")
        self.assertContains(response, "data-preview-run")
        self.assertContains(response, "Run the query to see the results.")
        self.assertNotContains(response, "preview-float")

    def test_home_omits_internal_project_copy(self):
        response = self.client.get(reverse("home"))

        self.assertNotContains(response, "Built for IT students")
        self.assertNotContains(response, "IT317")
        self.assertNotContains(response, "Cebu Institute")
        self.assertNotContains(response, "Sample databases, query feedback")


class AuthScreenTests(TestCase):
    def test_login_screen_has_expected_controls(self):
        response = self.client.get(reverse("login"))

        for text in (
            "Welcome back.",
            "Username or email",
            "Remember me",
            "Forgot password?",
            "Continue with Google",
            "Create account",
        ):
            self.assertContains(response, text)
        self.assertContains(response, "data-password-toggle")
        self.assertContains(response, "disabled")

    def test_signup_screen_has_expected_controls(self):
        response = self.client.get(reverse("signup"))

        for text in (
            "Create your account",
            "Full name",
            "First name",
            "Last name",
            "Username",
            "Email address",
            "Contact number",
            "Create account",
            "Continue with Google",
            "Log in",
        ):
            self.assertContains(response, text)
        self.assertContains(response, "data-password-toggle")

    def test_signup_placeholders_are_generic(self):
        response = self.client.get(reverse("signup"))

        self.assertContains(response, 'placeholder="First name"')
        self.assertContains(response, 'placeholder="Last name"')
        self.assertContains(response, 'placeholder="Phone number"')
        self.assertContains(response, 'placeholder="Choose a username"')
        self.assertNotContains(response, "Jamuel")
        self.assertNotContains(response, "Bacus")

    def test_signup_has_live_password_rules(self):
        response = self.client.get(reverse("signup"))

        for text in (
            "Your password must contain at least 8 characters.",
            "Your password can\u2019t be a commonly used password.",
            "Your password can\u2019t be entirely numeric.",
            "Your password can\u2019t be too similar to your other personal information.",
        ):
            self.assertContains(response, text)
        self.assertContains(response, "data-pw-rules")
        self.assertContains(response, "data-pw-match")


class AppChromeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="learner",
            email="learner@example.com",
            password="Str0ngPass!234",
        )
        self.client.force_login(self.user)

    def test_dashboard_uses_app_header(self):
        response = self.client.get(reverse("learner_dashboard"))

        self.assertContains(response, "data-app-header")
        self.assertContains(response, "Log out")
        self.assertNotContains(response, "FAQ")

    def test_profile_uses_app_header(self):
        response = self.client.get(reverse("profile"))

        self.assertContains(response, "data-app-header")
        self.assertContains(response, "Log out")
