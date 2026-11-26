from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.test import TestCase
from django.urls import reverse

from .models import SavedQuery
from .views import _is_last_active_administrator

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


class LastAdministratorGuardTests(TestCase):
    def setUp(self):
        self.first_admin = User.objects.create_user(
            username="guard-admin-1",
            email="guard-admin-1@example.com",
            password="Str0ngPass!234",
            role=User.Role.ADMINISTRATOR,
        )
        self.second_admin = User.objects.create_user(
            username="guard-admin-2",
            email="guard-admin-2@example.com",
            password="Str0ngPass!234",
            role=User.Role.ADMINISTRATOR,
        )
        self.client.force_login(self.first_admin)

    @staticmethod
    def _call_with_lock_spy(action):
        original_select_for_update = QuerySet.select_for_update
        locked_querysets = []

        def record(queryset):
            locked_queryset = original_select_for_update(queryset)
            locked_querysets.append(locked_queryset)
            return locked_queryset

        with patch.object(
            QuerySet,
            "select_for_update",
            autospec=True,
            side_effect=record,
        ):
            response = action()
        return response, locked_querysets

    def _assert_active_administrators_locked(self, locked_querysets):
        is_active_column = User._meta.get_field("is_active").column
        role_column = User._meta.get_field("role").column
        order_by = (
            f'ORDER BY "{User._meta.db_table}"."{User._meta.pk.column}" ASC'
        )
        locked_admin_querysets = []
        for queryset in locked_querysets:
            query = str(queryset.query)
            if (
                queryset.model is User
                and queryset.query.select_for_update
                and f'"{is_active_column}" = True' in query
                and f'"{role_column}" = ADMINISTRATOR' in query
                and order_by in query
            ):
                locked_admin_querysets.append(queryset)

        self.assertTrue(
            locked_admin_querysets,
            "Expected select_for_update() on the active-administrator queryset.",
        )

    def test_user_edit_locks_active_administrators_before_guard(self):
        def edit_admin():
            return self.client.post(
                reverse("user_edit", args=[self.second_admin.pk]),
                {
                    "username": self.second_admin.username,
                    "first_name": "Second",
                    "last_name": "Admin",
                    "email": self.second_admin.email,
                    "role": User.Role.LEARNER,
                    "is_active": "on",
                },
            )

        response, locked_querysets = self._call_with_lock_spy(edit_admin)

        self.assertRedirects(response, reverse("manage_users"))
        self._assert_active_administrators_locked(locked_querysets)
        self.second_admin.refresh_from_db()
        self.assertEqual(self.second_admin.role, User.Role.LEARNER)

    def test_user_delete_locks_active_administrators_before_guard(self):
        def delete_admin():
            return self.client.post(
                reverse("user_delete", args=[self.second_admin.pk])
            )

        response, locked_querysets = self._call_with_lock_spy(delete_admin)

        self.assertRedirects(response, reverse("manage_users"))
        self._assert_active_administrators_locked(locked_querysets)
        self.assertFalse(User.objects.filter(pk=self.second_admin.pk).exists())

    def test_edit_reports_error_when_locked_set_has_only_target(self):
        with patch(
            "dashboard.views._locked_active_administrators",
            return_value=[self.second_admin],
        ):
            response = self.client.post(
                reverse("user_edit", args=[self.second_admin.pk]),
                {
                    "username": self.second_admin.username,
                    "first_name": "Second",
                    "last_name": "Admin",
                    "email": self.second_admin.email,
                    "role": User.Role.LEARNER,
                    "is_active": "on",
                },
            )

        self.assertContains(response, "At least one active administrator must remain.")
        self.second_admin.refresh_from_db()
        self.assertEqual(self.second_admin.role, User.Role.ADMINISTRATOR)

    def test_delete_reports_error_when_locked_set_has_only_target(self):
        with patch(
            "dashboard.views._locked_active_administrators",
            return_value=[self.second_admin],
        ):
            response = self.client.post(
                reverse("user_delete", args=[self.second_admin.pk])
            )

        self.assertRedirects(
            response, reverse("user_delete", args=[self.second_admin.pk])
        )
        self.assertTrue(User.objects.filter(pk=self.second_admin.pk).exists())

    def test_guard_recognizes_last_active_administrator_from_locked_set(self):
        User.objects.filter(pk=self.second_admin.pk).update(is_active=False)

        self.assertTrue(
            _is_last_active_administrator(self.first_admin, [self.first_admin])
        )
        self.assertFalse(
            _is_last_active_administrator(self.second_admin, [self.first_admin])
        )


class SavedQueryTransactionTests(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            username="transaction-owner",
            email="transaction-owner@example.com",
            password="Str0ngPass!234",
        )
        self.client.force_login(self.learner)

    def test_create_failure_after_write_rolls_back(self):
        with patch(
            "dashboard.views.messages.success", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse("saved_query_create"),
                    {"title": "Rollback", "sql": "SELECT 1;"},
                )

        self.assertFalse(
            SavedQuery.objects.filter(user=self.learner, title="Rollback").exists()
        )

    def test_edit_failure_after_write_rolls_back(self):
        saved_query = SavedQuery.objects.create(
            user=self.learner,
            title="Original",
            sql="SELECT original;",
        )

        with patch(
            "dashboard.views.messages.success", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse("saved_query_edit", args=[saved_query.pk]),
                    {"title": "Changed", "sql": "SELECT changed;"},
                )

        saved_query.refresh_from_db()
        self.assertEqual(saved_query.title, "Original")
        self.assertEqual(saved_query.sql, "SELECT original;")


class UserManagementTransactionTests(TestCase):
    def setUp(self):
        self.administrator = User.objects.create_user(
            username="tx-admin",
            email="tx-admin@example.com",
            password="Str0ngPass!234",
            role=User.Role.ADMINISTRATOR,
        )
        self.learner = User.objects.create_user(
            username="tx-learner",
            email="tx-learner@example.com",
            password="Str0ngPass!234",
        )
        self.client.force_login(self.administrator)

    def test_edit_failure_after_save_rolls_back(self):
        with patch(
            "dashboard.views.messages.success", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse("user_edit", args=[self.learner.pk]),
                    {
                        "username": "tx-learner",
                        "first_name": "Changed",
                        "last_name": "User",
                        "email": "tx-learner@example.com",
                        "role": User.Role.ADMINISTRATOR,
                        "is_active": "on",
                    },
                )

        self.learner.refresh_from_db()
        self.assertEqual(self.learner.role, User.Role.LEARNER)
        self.assertEqual(self.learner.first_name, "")

    def test_password_failure_after_save_rolls_back(self):
        with patch(
            "dashboard.views.messages.success", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse("user_password", args=[self.learner.pk]),
                    {
                        "password1": "N3wStr0ngPass!",
                        "password2": "N3wStr0ngPass!",
                    },
                )

        self.learner.refresh_from_db()
        self.assertTrue(self.learner.check_password("Str0ngPass!234"))

    def test_delete_failure_after_delete_rolls_back(self):
        with patch(
            "dashboard.views.messages.success", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse("user_delete", args=[self.learner.pk])
                )

        self.assertTrue(User.objects.filter(pk=self.learner.pk).exists())
