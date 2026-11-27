from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models import QueryHistory, SavedQuery
User = get_user_model()
from dashboard.forms import AdminUserCreateForm, AdminUserEditForm
from datetime import timedelta
from unittest.mock import patch
from django.contrib.messages import get_messages
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import PositiveIntegerField
from django.db.models.query import QuerySet
from django.test import Client, TestCase, TransactionTestCase
from sqlplayground.test_helpers import csrf_token_from_response, post_with_csrf_token
from .models import QueryHistory, SavedQuery
from .views import _is_last_active_administrator

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

    def test_create_user_rejects_case_variant_username(self):
        response = self.client.post(
            reverse("user_create"),
            {
                "username": "LEARNER1",
                "first_name": "New",
                "last_name": "User",
                "email": "newuser@example.com",
                "role": User.Role.LEARNER,
                "is_active": "on",
                "password1": "Str0ngPass!234",
                "password2": "Str0ngPass!234",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["form"].errors)
        self.assertFalse(User.objects.filter(email="newuser@example.com").exists())

    def test_create_user_rejects_case_variant_email(self):
        response = self.client.post(
            reverse("user_create"),
            {
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "email": "LEARNER1@example.com",
                "role": User.Role.LEARNER,
                "is_active": "on",
                "password1": "Str0ngPass!234",
                "password2": "Str0ngPass!234",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "An account with this email address already exists."
        )
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_edit_user_rejects_case_variant_username(self):
        response = self.client.post(
            reverse("user_edit", args=[self.learner.pk]),
            {
                "username": "ADMIN1",
                "first_name": "Learner",
                "last_name": "One",
                "email": "learner1@example.com",
                "role": User.Role.LEARNER,
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["form"].errors)
        self.learner.refresh_from_db()
        self.assertEqual(self.learner.username, "learner1")

    def test_edit_user_rejects_case_variant_email(self):
        response = self.client.post(
            reverse("user_edit", args=[self.learner.pk]),
            {
                "username": "learner1",
                "first_name": "Learner",
                "last_name": "One",
                "email": "ADMIN1@example.com",
                "role": User.Role.LEARNER,
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "An account with this email address already exists."
        )
        self.learner.refresh_from_db()
        self.assertEqual(self.learner.email, "learner1@example.com")

    def test_edit_user_accepts_own_case_variant_identifiers(self):
        response = self.client.post(
            reverse("user_edit", args=[self.learner.pk]),
            {
                "username": "LEARNER1",
                "first_name": "Learner",
                "last_name": "One",
                "email": "LEARNER1@example.com",
                "role": User.Role.LEARNER,
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("manage_users"))
        self.learner.refresh_from_db()
        self.assertEqual(self.learner.username, "LEARNER1")
        self.assertEqual(self.learner.email, "learner1@example.com")

class PaginationTests(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            username="learner",
            email="learner@example.com",
            password="Str0ngPass!234",
        )
        self.other = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="Str0ngPass!234",
        )
        self.administrator = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="Str0ngPass!234",
            role=User.Role.ADMINISTRATOR,
        )
        for index in range(3):
            SavedQuery.objects.create(
                user=self.other, title=f"Theirs {index}", sql="SELECT 2;"
            )
            QueryHistory.objects.create(user=self.other, sql="SELECT 999;")
        for index in range(25):
            SavedQuery.objects.create(
                user=self.learner, title=f"Mine {index}", sql="SELECT 1;"
            )
            QueryHistory.objects.create(user=self.learner, sql=f"SELECT {index};")
        self.client.force_login(self.learner)

    def test_saved_query_list_pages_are_boundary_correct_and_user_scoped(self):
        first = self.client.get(reverse("saved_query_list"))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.context["page_obj"].paginator.count, 25)
        self.assertEqual(len(first.context["page_obj"].object_list), 10)
        self.assertTrue(first.context["page_obj"].has_next())
        self.assertNotContains(first, "Theirs 0")

        second = self.client.get(reverse("saved_query_list"), {"page": 2})
        self.assertEqual(second.context["page_obj"].number, 2)
        self.assertEqual(len(second.context["page_obj"].object_list), 10)
        self.assertNotContains(second, "Theirs 0")

        third = self.client.get(reverse("saved_query_list"), {"page": 3})
        self.assertEqual(len(third.context["page_obj"].object_list), 5)
        self.assertFalse(third.context["page_obj"].has_next())
        self.assertNotContains(third, "Theirs 0")

    def test_saved_query_list_handles_invalid_page_numbers(self):
        out_of_range = self.client.get(reverse("saved_query_list"), {"page": 999})
        self.assertEqual(out_of_range.status_code, 200)
        self.assertEqual(out_of_range.context["page_obj"].number, 3)
        self.assertEqual(len(out_of_range.context["page_obj"].object_list), 5)

        malformed = self.client.get(reverse("saved_query_list"), {"page": "abc"})
        self.assertEqual(malformed.status_code, 200)
        self.assertEqual(malformed.context["page_obj"].number, 1)

    def test_saved_query_list_preserves_query_parameters(self):
        response = self.client.get(
            reverse("saved_query_list"), {"view": "compact", "page": 2}
        )

        self.assertEqual(response.context["querystring"], "view=compact")
        self.assertContains(response, "view=compact")
        self.assertEqual(len(response.context["saved_queries"].object_list), 10)

    def test_query_history_page_is_paginated_and_user_scoped(self):
        first = self.client.get(reverse("query_history_list"))
        self.assertEqual(first.status_code, 200)
        self.assertTemplateUsed(first, "dashboard/history.html")
        self.assertEqual(first.context["page_obj"].paginator.count, 25)
        self.assertEqual(len(first.context["page_obj"].object_list), 10)
        self.assertNotContains(first, "SELECT 999;")

        last = self.client.get(reverse("query_history_list"), {"page": 3})
        self.assertEqual(len(last.context["page_obj"].object_list), 5)
        self.assertFalse(last.context["page_obj"].has_next())
        self.assertNotContains(last, "SELECT 999;")

    def test_query_history_page_handles_invalid_page_numbers(self):
        out_of_range = self.client.get(reverse("query_history_list"), {"page": 999})
        self.assertEqual(out_of_range.status_code, 200)
        self.assertEqual(out_of_range.context["page_obj"].number, 3)

        malformed = self.client.get(reverse("query_history_list"), {"page": "abc"})
        self.assertEqual(malformed.status_code, 200)
        self.assertEqual(malformed.context["page_obj"].number, 1)

    def test_query_history_page_shows_empty_state(self):
        empty_user = User.objects.create_user(
            username="empty",
            email="empty@example.com",
            password="Str0ngPass!234",
        )
        self.client.force_login(empty_user)

        response = self.client.get(reverse("query_history_list"))

        self.assertEqual(response.context["page_obj"].paginator.count, 0)
        self.assertContains(response, "No query history yet.")

    def test_manage_users_ordering_breaks_date_ties_by_pk(self):
        shared_date = timezone.now()
        for index in range(1, 4):
            User.objects.create_user(
                username=f"tie{index}",
                email=f"tie{index}@example.com",
                password="Str0ngPass!234",
                date_joined=shared_date,
            )
        self.client.force_login(self.administrator)

        response = self.client.get(reverse("manage_users"))
        usernames = [user.username for user in response.context["page_obj"].object_list]

        self.assertLess(usernames.index("tie3"), usernames.index("tie2"))
        self.assertLess(usernames.index("tie2"), usernames.index("tie1"))

    def test_manage_users_preserves_filters_across_pages(self):
        self.client.force_login(self.administrator)
        for index in range(25):
            User.objects.create_user(
                username=f"filtered{index}",
                email=f"filtered{index}@example.com",
                password="Str0ngPass!234",
            )

        response = self.client.get(
            reverse("manage_users"),
            {"q": "filtered", "role": "LEARNER", "page": 2},
        )

        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertIn("q=filtered", response.context["querystring"])
        self.assertIn("role=LEARNER", response.context["querystring"])
        self.assertNotIn("page=", response.context["querystring"])
        self.assertContains(response, "q=filtered")

class QueryCountRegressionTests(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            username="learner",
            email="learner@example.com",
            password="Str0ngPass!234",
        )
        self.administrator = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="Str0ngPass!234",
            role=User.Role.ADMINISTRATOR,
        )
        for index in range(5):
            SavedQuery.objects.create(
                user=self.learner, title=f"Query {index}", sql="SELECT 1;"
            )
            QueryHistory.objects.create(
                user=self.learner, sql="SELECT 1;", status="success"
            )
            User.objects.create_user(
                username=f"user{index}",
                email=f"user{index}@example.com",
                password="Str0ngPass!234",
            )

    def test_learner_dashboard_query_count(self):
        self.client.force_login(self.learner)

        with self.assertNumQueries(5):
            response = self.client.get(reverse("learner_dashboard"))

        self.assertEqual(response.status_code, 200)

    def test_administrator_dashboard_query_count(self):
        self.client.force_login(self.administrator)

        with self.assertNumQueries(4):
            response = self.client.get(reverse("administrator_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_learners"], 6)
        self.assertEqual(response.context["total_administrators"], 1)

    def test_saved_query_list_query_count(self):
        self.client.force_login(self.learner)

        with self.assertNumQueries(4):
            response = self.client.get(reverse("saved_query_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["saved_queries"]), 5)

    def test_sandbox_query_history_query_count(self):
        self.client.force_login(self.learner)

        with self.assertNumQueries(4):
            response = self.client.get(reverse("sandbox"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["query_history"]), 5)

    def test_sandbox_history_user_is_already_loaded(self):
        self.client.force_login(self.learner)
        response = self.client.get(reverse("sandbox"))
        histories = list(response.context["query_history"])

        with self.assertNumQueries(0):
            rendered = [str(item) for item in histories]

        self.assertTrue(all(text.startswith("learner: ") for text in rendered))

    def test_manage_users_query_count(self):
        self.client.force_login(self.administrator)

        with self.assertNumQueries(4):
            response = self.client.get(reverse("manage_users"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_count"], 7)
        self.assertEqual(len(response.context["page_obj"].object_list), 7)

class AdminContactNumberFormTests(TestCase):
    CONTACT_ERROR = "Enter a valid contact number (7-15 digits, optional leading +)."

    def setUp(self):
        self.target = User.objects.create_user(
            username="learner1",
            email="learner1@example.com",
            password="Str0ngPass!234",
        )
        self.create_data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "contact_number": "+639171234567",
            "role": User.Role.LEARNER,
            "is_active": "on",
            "password1": "Str0ngPass!234",
            "password2": "Str0ngPass!234",
        }
        self.edit_data = {
            "username": "learner1",
            "first_name": "Learner",
            "last_name": "One",
            "email": "learner1@example.com",
            "contact_number": "+639171234567",
            "role": User.Role.LEARNER,
            "is_active": "on",
        }

    def test_create_form_accepts_a_valid_contact_number(self):
        form = AdminUserCreateForm(self.create_data)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["contact_number"], "+639171234567")

    def test_create_form_rejects_an_invalid_contact_number(self):
        form = AdminUserCreateForm(
            {**self.create_data, "contact_number": "abc123"}
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["contact_number"], [self.CONTACT_ERROR])

    def test_edit_form_accepts_a_valid_contact_number(self):
        form = AdminUserEditForm(self.edit_data, instance=self.target)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().contact_number, "+639171234567")

    def test_edit_form_rejects_an_invalid_contact_number(self):
        form = AdminUserEditForm(
            {**self.edit_data, "contact_number": "123"}, instance=self.target
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["contact_number"], [self.CONTACT_ERROR])

class AdminUserFormUniquenessTests(TestCase):
    def setUp(self):
        self.target = User.objects.create_user(
            username="learner1",
            email="learner1@example.com",
            password="Str0ngPass!234",
        )
        self.other = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="Str0ngPass!234",
            role=User.Role.ADMINISTRATOR,
        )
        self.create_data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "role": User.Role.LEARNER,
            "is_active": "on",
            "password1": "Str0ngPass!234",
            "password2": "Str0ngPass!234",
        }
        self.edit_data = {
            "username": "learner1",
            "first_name": "Learner",
            "last_name": "One",
            "email": "learner1@example.com",
            "role": User.Role.LEARNER,
            "is_active": "on",
        }

    def test_create_form_rejects_case_variant_username(self):
        form = AdminUserCreateForm({**self.create_data, "username": "ADMIN1"})

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["username"], ["This username is already taken."]
        )

    def test_create_form_rejects_case_variant_email(self):
        form = AdminUserCreateForm(
            {**self.create_data, "email": "ADMIN1@example.com"}
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["email"],
            ["An account with this email address already exists."],
        )

    def test_create_form_accepts_a_new_email(self):
        form = AdminUserCreateForm(self.create_data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_edit_form_rejects_case_variant_username(self):
        form = AdminUserEditForm(
            {**self.edit_data, "username": "ADMIN1"}, instance=self.target
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["username"], ["This username is already taken."]
        )

    def test_edit_form_rejects_case_variant_email(self):
        form = AdminUserEditForm(
            {**self.edit_data, "email": "ADMIN1@example.com"},
            instance=self.target,
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["email"],
            ["An account with this email address already exists."],
        )

    def test_edit_form_allows_the_accounts_own_case_variant_identifiers(self):
        form = AdminUserEditForm(
            {
                **self.edit_data,
                "username": "LEARNER1",
                "email": "LEARNER1@example.com",
            },
            instance=self.target,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["email"], "learner1@example.com")

class AdminUserFormNormalizationTests(TestCase):
    def setUp(self):
        self.target = User.objects.create_user(
            username="learner1",
            email="learner1@example.com",
            password="Str0ngPass!234",
        )

    def test_create_form_strips_whitespace_and_preserves_username_case(self):
        form = AdminUserCreateForm(
            {
                "username": "  NewUser  ",
                "first_name": "New",
                "last_name": "User",
                "email": "  New.User@Example.com  ",
                "role": User.Role.LEARNER,
                "is_active": "on",
                "password1": "Str0ngPass!234",
                "password2": "Str0ngPass!234",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["username"], "NewUser")
        self.assertEqual(form.cleaned_data["email"], "new.user@example.com")

    def test_edit_form_strips_whitespace_and_preserves_username_case(self):
        form = AdminUserEditForm(
            {
                "username": "  LEARNER1  ",
                "first_name": "Learner",
                "last_name": "One",
                "email": "  LEARNER1@EXAMPLE.COM  ",
                "role": User.Role.LEARNER,
                "is_active": "on",
            },
            instance=self.target,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["username"], "LEARNER1")
        self.assertEqual(form.cleaned_data["email"], "learner1@example.com")

class SavedQueryCsrfTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.learner = User.objects.create_user(
            username="learner1",
            email="learner1@example.com",
            password="Str0ngPass!234",
        )
        self.client.force_login(self.learner)
        self.saved_query = SavedQuery.objects.create(
            user=self.learner,
            title="All students",
            sql="SELECT * FROM students;",
        )

    def test_create_rejects_post_without_token(self):
        response = self.client.post(
            reverse("saved_query_create"),
            {"title": "Courses", "sql": "SELECT * FROM courses;"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(SavedQuery.objects.filter(user=self.learner).count(), 1)

    def test_create_rejects_invalid_token(self):
        url = reverse("saved_query_create")
        token = csrf_token_from_response(self.client.get(url), url)
        response = self.client.post(
            reverse("saved_query_create"),
            {
                "title": "Courses",
                "sql": "SELECT * FROM courses;",
                "csrfmiddlewaretoken": f"invalid-{token}",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(SavedQuery.objects.filter(user=self.learner).count(), 1)

    def test_create_accepts_valid_token(self):
        url = reverse("saved_query_create")
        response = post_with_csrf_token(
            self.client,
            url,
            url,
            {"title": "Courses", "sql": "SELECT * FROM courses;"},
        )

        created = SavedQuery.objects.get(user=self.learner, title="Courses")
        self.assertRedirects(
            response, reverse("saved_query_detail", args=[created.pk])
        )
        self.assertEqual(created.sql, "SELECT * FROM courses;")
        self.assertEqual(SavedQuery.objects.filter(user=self.learner).count(), 2)

    def test_edit_rejects_post_without_token(self):
        response = self.client.post(
            reverse("saved_query_edit", args=[self.saved_query.pk]),
            {"title": "Renamed", "sql": "SELECT 1;"},
        )

        self.assertEqual(response.status_code, 403)
        self.saved_query.refresh_from_db()
        self.assertEqual(self.saved_query.title, "All students")
        self.assertEqual(self.saved_query.sql, "SELECT * FROM students;")

    def test_edit_accepts_valid_token(self):
        url = reverse("saved_query_edit", args=[self.saved_query.pk])
        response = post_with_csrf_token(
            self.client,
            url,
            url,
            {"title": "Renamed", "sql": "SELECT 1;"},
        )

        self.assertRedirects(
            response, reverse("saved_query_detail", args=[self.saved_query.pk])
        )
        self.saved_query.refresh_from_db()
        self.assertEqual(self.saved_query.title, "Renamed")
        self.assertEqual(self.saved_query.sql, "SELECT 1;")

    def test_delete_rejects_post_without_token(self):
        response = self.client.post(
            reverse("saved_query_delete", args=[self.saved_query.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(SavedQuery.objects.filter(pk=self.saved_query.pk).exists())

    def test_delete_accepts_valid_token(self):
        response = post_with_csrf_token(
            self.client,
            reverse("saved_query_detail", args=[self.saved_query.pk]),
            reverse("saved_query_delete", args=[self.saved_query.pk]),
            {},
        )

        self.assertRedirects(response, reverse("saved_query_list"))
        self.assertFalse(SavedQuery.objects.filter(pk=self.saved_query.pk).exists())

class UserManagementCsrfTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
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
        self.create_data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "role": User.Role.LEARNER,
            "is_active": "on",
            "password1": "Str0ngPass!234",
            "password2": "Str0ngPass!234",
        }
        self.edit_data = {
            "username": "learner1",
            "first_name": "Learner",
            "last_name": "One",
            "email": "learner1@example.com",
            "role": User.Role.ADMINISTRATOR,
        }
        self.password_data = {
            "password1": "N3wStr0ngPass!",
            "password2": "N3wStr0ngPass!",
        }

    def test_user_create_rejects_post_without_token(self):
        response = self.client.post(reverse("user_create"), self.create_data)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_user_create_accepts_valid_token(self):
        token_page = reverse("user_create")
        response = post_with_csrf_token(
            self.client, token_page, reverse("user_create"), self.create_data
        )

        self.assertRedirects(response, reverse("manage_users"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_user_edit_rejects_post_without_token(self):
        response = self.client.post(
            reverse("user_edit", args=[self.learner.pk]), self.edit_data
        )

        self.assertEqual(response.status_code, 403)
        self.learner.refresh_from_db()
        self.assertEqual(self.learner.role, User.Role.LEARNER)
        self.assertTrue(self.learner.is_active)

    def test_user_edit_accepts_valid_token(self):
        url = reverse("user_edit", args=[self.learner.pk])
        response = post_with_csrf_token(self.client, url, url, self.edit_data)

        self.assertRedirects(response, reverse("manage_users"))
        self.learner.refresh_from_db()
        self.assertEqual(self.learner.role, User.Role.ADMINISTRATOR)

    def test_password_change_rejects_post_without_token(self):
        response = self.client.post(
            reverse("user_password", args=[self.learner.pk]), self.password_data
        )

        self.assertEqual(response.status_code, 403)
        self.learner.refresh_from_db()
        self.assertTrue(self.learner.check_password("Str0ngPass!234"))
        self.assertFalse(self.learner.check_password("N3wStr0ngPass!"))

    def test_password_change_accepts_valid_token(self):
        url = reverse("user_password", args=[self.learner.pk])
        response = post_with_csrf_token(self.client, url, url, self.password_data)

        self.assertRedirects(response, reverse("user_edit", args=[self.learner.pk]))
        self.learner.refresh_from_db()
        self.assertTrue(self.learner.check_password("N3wStr0ngPass!"))

    def test_user_delete_rejects_post_without_token(self):
        response = self.client.post(
            reverse("user_delete", args=[self.learner.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.learner.pk).exists())

    def test_user_delete_accepts_valid_token(self):
        url = reverse("user_delete", args=[self.learner.pk])
        response = post_with_csrf_token(self.client, url, url, {})

        self.assertRedirects(response, reverse("manage_users"))
        self.assertFalse(User.objects.filter(pk=self.learner.pk).exists())

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
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor, SavedQuery._meta.db_table
            )
        self.assertIn("savedquery_user_recent_idx", constraints)

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
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor, QueryHistory._meta.db_table
            )
        self.assertIn("queryhistory_user_recent_idx", constraints)

class SavedQueryDuplicateHandlingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="duplicate-owner",
            email="duplicate-owner@example.com",
            password="Str0ngPass!234",
        )
        self.existing = SavedQuery.objects.create(
            user=self.user,
            title="Top Students",
            sql="SELECT first_name FROM students;",
        )
        self.client.force_login(self.user)

    def messages_text(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def test_create_with_duplicate_title_shows_error_instead_of_crashing(self):
        response = self.client.post(
            reverse("saved_query_create"),
            {"title": "top students", "sql": "SELECT last_name FROM students;"},
        )

        self.assertRedirects(response, reverse("saved_query_list"))
        self.assertTrue(
            any("already exists" in text for text in self.messages_text(response))
        )
        self.assertEqual(SavedQuery.objects.filter(user=self.user).count(), 1)

    def test_edit_to_duplicate_title_shows_error_and_keeps_original(self):
        other = SavedQuery.objects.create(
            user=self.user,
            title="Other Query",
            sql="SELECT 1;",
        )

        response = self.client.post(
            reverse("saved_query_edit", args=[other.pk]),
            {"title": "TOP STUDENTS", "sql": "SELECT 2;"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any("already exists" in text for text in self.messages_text(response))
        )
        other.refresh_from_db()
        self.assertEqual(other.title, "Other Query")
        self.assertEqual(other.sql, "SELECT 1;")
        self.existing.refresh_from_db()
        self.assertEqual(self.existing.title, "Top Students")

class SavedQueryMigrationIntegrityTests(TransactionTestCase):
    migrate_from = [("dashboard", "0001_initial")]
    migrate_to = [
        ("dashboard", "0002_alter_queryhistory_row_count_and_more")
    ]

    def setUp(self):
        executor = MigrationExecutor(connection)
        self.latest_nodes = executor.loader.graph.leaf_nodes()
        self.addCleanup(self.restore_latest_migrations)
        executor.migrate(self.migrate_from)
        self.apps_before = executor.loader.project_state(self.migrate_from).apps
        super().setUp()

    def restore_latest_migrations(self):
        MigrationExecutor(connection).migrate(self.latest_nodes)

    def test_deduplicates_existing_case_variant_titles(self):
        User = self.apps_before.get_model("accounts", "CustomUser")
        SavedQuery = self.apps_before.get_model("dashboard", "SavedQuery")
        user = User.objects.create_user(
            username="legacy-owner",
            email="legacy-owner@example.com",
            password="Str0ngPass!234",
        )
        older = SavedQuery.objects.create(
            user=user, title="Top Students", sql="SELECT old;"
        )
        newer = SavedQuery.objects.create(
            user=user, title="top students", sql="SELECT new;"
        )
        SavedQuery.objects.filter(pk=older.pk).update(
            updated_at=timezone.now() - timedelta(minutes=5)
        )
        SavedQuery.objects.filter(pk=newer.pk).update(updated_at=timezone.now())

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)

        SavedQueryAfter = (
            executor.loader.project_state(self.migrate_to)
            .apps.get_model("dashboard", "SavedQuery")
        )
        rows = list(SavedQueryAfter.objects.filter(user_id=user.pk))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].sql, "SELECT new;")
