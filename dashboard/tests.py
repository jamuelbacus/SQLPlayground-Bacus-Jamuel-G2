from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import PositiveIntegerField
from django.test import TestCase
from django.urls import reverse

from .models import QueryHistory, SavedQuery

User = get_user_model()


class DashboardAccessTests(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            username="learner1",
            email="learner1@example.com",
            password="Str0ngPass!234",
            first_name="Learner",
            last_name="One",
        )
        self.administrator = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="Str0ngPass!234",
            first_name="Admin",
            last_name="One",
            role=User.Role.ADMINISTRATOR,
        )

    def test_anonymous_user_is_sent_to_login_from_learner_dashboard(self):
        response = self.client.get(reverse("learner_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_anonymous_user_is_sent_to_login_from_administrator_dashboard(self):
        response = self.client.get(reverse("administrator_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_learner_can_open_learner_dashboard(self):
        self.client.force_login(self.learner)

        response = self.client.get(reverse("learner_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/learner_dashboard.html")

    def test_learner_cannot_open_administrator_dashboard(self):
        self.client.force_login(self.learner)

        response = self.client.get(reverse("administrator_dashboard"))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")

    def test_administrator_can_open_administrator_dashboard(self):
        self.client.force_login(self.administrator)

        response = self.client.get(reverse("administrator_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/administrator_dashboard.html")

    def test_administrator_cannot_open_learner_dashboard(self):
        self.client.force_login(self.administrator)

        response = self.client.get(reverse("learner_dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_dashboard_redirect_sends_learner_to_learner_dashboard(self):
        self.client.force_login(self.learner)

        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, reverse("learner_dashboard"))

    def test_dashboard_redirect_sends_administrator_to_administrator_dashboard(self):
        self.client.force_login(self.administrator)

        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, reverse("administrator_dashboard"))

    def test_superuser_is_always_an_administrator(self):
        superuser = User.objects.create_superuser(
            username="root",
            email="root@example.com",
            password="Str0ngPass!234",
        )

        self.assertEqual(superuser.role, User.Role.ADMINISTRATOR)


class AdministratorDashboardContentTests(TestCase):
    def setUp(self):
        self.administrator = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="Str0ngPass!234",
            role=User.Role.ADMINISTRATOR,
        )
        User.objects.create_user(
            username="learner1",
            email="learner1@example.com",
            password="Str0ngPass!234",
        )
        self.client.force_login(self.administrator)

    def test_dashboard_shows_active_account_totals(self):
        response = self.client.get(reverse("administrator_dashboard"))

        self.assertEqual(response.context["total_learners"], 1)
        self.assertEqual(response.context["total_administrators"], 1)
        self.assertNotIn("total_users", response.context)
        self.assertContains(response, "Recent Registrations")
        self.assertContains(response, reverse("manage_users"))
        self.assertNotContains(response, "Total accounts")
        self.assertNotContains(response, "Administrator tools")
        self.assertNotContains(response, "Role reminder")
        self.assertNotContains(response, "Django admin")


class UserManagementAccessTests(TestCase):
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

    def test_anonymous_user_is_sent_to_login_from_manage_users(self):
        response = self.client.get(reverse("manage_users"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_learner_cannot_open_manage_users(self):
        self.client.force_login(self.learner)

        response = self.client.get(reverse("manage_users"))

        self.assertEqual(response.status_code, 403)

    def test_administrator_can_open_manage_users(self):
        self.client.force_login(self.administrator)

        response = self.client.get(reverse("manage_users"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/manage_users.html")
        self.assertContains(response, "Manage Users")
        self.assertContains(response, "Create User")


class UserManagementTests(TestCase):
    def setUp(self):
        self.administrator = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="Str0ngPass!234",
            role=User.Role.ADMINISTRATOR,
        )
        self.learner = User.objects.create_user(
            username="learner1",
            email="learner1@example.com",
            password="Str0ngPass!234",
            first_name="Learner",
            last_name="One",
        )
        self.client.force_login(self.administrator)

    def test_manage_users_lists_accounts(self):
        response = self.client.get(reverse("manage_users"))

        self.assertContains(response, "admin1@example.com")
        self.assertContains(response, "learner1@example.com")
        self.assertContains(response, "learner1")
        self.assertContains(response, "2 accounts")

    def test_search_filters_accounts(self):
        response = self.client.get(reverse("manage_users"), {"q": "learner1"})

        self.assertContains(response, "learner1@example.com")
        self.assertNotContains(response, "admin1@example.com")
        self.assertContains(response, "1 account")

    def test_role_filter_limits_accounts(self):
        response = self.client.get(reverse("manage_users"), {"role": "LEARNER"})

        self.assertContains(response, "learner1@example.com")
        self.assertNotContains(response, "admin1@example.com")

    def test_status_filter_limits_accounts(self):
        User.objects.create_user(
            username="inactive1",
            email="inactive1@example.com",
            password="Str0ngPass!234",
            is_active=False,
        )

        response = self.client.get(reverse("manage_users"), {"status": "inactive"})

        self.assertContains(response, "inactive1@example.com")
        self.assertNotContains(response, "learner1@example.com")
        self.assertNotContains(response, "admin1@example.com")

    def test_create_user_creates_an_account(self):
        response = self.client.post(
            reverse("user_create"),
            {
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "email": "newuser@example.com",
                "role": User.Role.LEARNER,
                "is_active": "on",
                "password1": "Str0ngPass!234",
                "password2": "Str0ngPass!234",
            },
        )

        self.assertRedirects(response, reverse("manage_users"))
        account = User.objects.get(username="newuser")
        self.assertEqual(account.email, "newuser@example.com")
        self.assertTrue(account.check_password("Str0ngPass!234"))

    def test_edit_user_updates_role_and_status(self):
        response = self.client.post(
            reverse("user_edit", args=[self.learner.pk]),
            {
                "username": "learner1",
                "first_name": "Learner",
                "last_name": "One",
                "email": "learner1@example.com",
                "role": User.Role.ADMINISTRATOR,
            },
        )

        self.assertRedirects(response, reverse("manage_users"))
        self.learner.refresh_from_db()
        self.assertEqual(self.learner.role, User.Role.ADMINISTRATOR)
        self.assertFalse(self.learner.is_active)

    def test_self_edit_cannot_demote_or_deactivate_own_account(self):
        response = self.client.post(
            reverse("user_edit", args=[self.administrator.pk]),
            {
                "username": "admin1",
                "first_name": "Admin",
                "last_name": "One",
                "email": "admin1@example.com",
                "role": User.Role.LEARNER,
            },
        )

        self.assertRedirects(response, reverse("manage_users"))
        self.administrator.refresh_from_db()
        self.assertEqual(self.administrator.role, User.Role.ADMINISTRATOR)
        self.assertTrue(self.administrator.is_active)

    def test_password_change_updates_the_account_password(self):
        response = self.client.post(
            reverse("user_password", args=[self.learner.pk]),
            {
                "password1": "N3wStr0ngPass!",
                "password2": "N3wStr0ngPass!",
            },
        )

        self.assertRedirects(
            response, reverse("user_edit", args=[self.learner.pk])
        )
        self.learner.refresh_from_db()
        self.assertTrue(self.learner.check_password("N3wStr0ngPass!"))

    def test_delete_user_removes_the_account(self):
        response = self.client.post(
            reverse("user_delete", args=[self.learner.pk])
        )

        self.assertRedirects(response, reverse("manage_users"))
        self.assertFalse(User.objects.filter(pk=self.learner.pk).exists())

    def test_administrator_cannot_delete_own_account(self):
        response = self.client.post(
            reverse("user_delete", args=[self.administrator.pk])
        )

        self.assertRedirects(response, reverse("manage_users"))
        self.assertTrue(User.objects.filter(pk=self.administrator.pk).exists())


class SavedQueryConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="saved-owner",
            email="saved-owner@example.com",
            password="Str0ngPass!234",
        )
        self.other_user = User.objects.create_user(
            username="other-owner",
            email="other-owner@example.com",
            password="Str0ngPass!234",
        )

    def create_saved_query(self, user, title):
        return SavedQuery.objects.create(user=user, title=title, sql="SELECT 1;")

    def test_exact_duplicate_title_for_same_user_is_rejected(self):
        self.create_saved_query(self.user, "Top Students")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_saved_query(self.user, "Top Students")

    def test_case_variant_duplicate_title_for_same_user_is_rejected(self):
        self.create_saved_query(self.user, "Top Students")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_saved_query(self.user, "top students")

    def test_same_title_for_different_users_is_allowed(self):
        self.create_saved_query(self.user, "Top Students")
        self.create_saved_query(self.other_user, "Top Students")

        self.assertEqual(SavedQuery.objects.filter(title="Top Students").count(), 2)

    def test_saved_query_recent_index_is_declared(self):
        index = next(
            index
            for index in SavedQuery._meta.indexes
            if index.name == "savedquery_user_recent_idx"
        )

        self.assertEqual(index.fields, ["user", "-updated_at", "-created_at"])


class QueryHistoryConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="history-owner",
            email="history-owner@example.com",
            password="Str0ngPass!234",
        )

    def test_invalid_status_is_rejected_at_database_level(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                QueryHistory.objects.create(
                    user=self.user,
                    sql="SELECT 1;",
                    status="pending",
                )

    def test_negative_row_count_is_rejected_at_database_level(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                QueryHistory.objects.create(
                    user=self.user,
                    sql="SELECT 1;",
                    row_count=-1,
                )

    def test_zero_and_positive_row_counts_are_allowed(self):
        zero = QueryHistory.objects.create(user=self.user, sql="SELECT 1;")
        positive = QueryHistory.objects.create(
            user=self.user,
            sql="SELECT 1;",
            row_count=12,
        )

        self.assertEqual(zero.row_count, 0)
        self.assertEqual(positive.row_count, 12)

    def test_row_count_uses_positive_integer_field(self):
        field = QueryHistory._meta.get_field("row_count")

        self.assertIsInstance(field, PositiveIntegerField)

    def test_query_history_recent_index_is_declared(self):
        index = next(
            index
            for index in QueryHistory._meta.indexes
            if index.name == "queryhistory_user_recent_idx"
        )

        self.assertEqual(index.fields, ["user", "-executed_at"])
