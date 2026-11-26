from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from sqlplayground.test_helpers import csrf_token_from_response, post_with_csrf_token

from .models import SavedQuery

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
        token = csrf_token_from_response(
            self.client.get(reverse("saved_query_create"))
        )
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
        token_page = reverse("manage_users")
        response = post_with_csrf_token(
            self.client, token_page, reverse("user_create"), self.create_data
        )

        self.assertRedirects(response, token_page)
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
        token_page = reverse("manage_users")
        url = reverse("user_edit", args=[self.learner.pk])
        response = post_with_csrf_token(self.client, token_page, url, self.edit_data)

        self.assertRedirects(response, token_page)
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
        token_page = reverse("manage_users")
        url = reverse("user_password", args=[self.learner.pk])
        response = post_with_csrf_token(
            self.client, token_page, url, self.password_data
        )

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
        token_page = reverse("manage_users")
        response = post_with_csrf_token(
            self.client,
            token_page,
            reverse("user_delete", args=[self.learner.pk]),
            {},
        )

        self.assertRedirects(response, token_page)
        self.assertFalse(User.objects.filter(pk=self.learner.pk).exists())
