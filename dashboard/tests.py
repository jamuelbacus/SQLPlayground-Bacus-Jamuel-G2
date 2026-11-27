from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models import QueryHistory, SavedQuery

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
