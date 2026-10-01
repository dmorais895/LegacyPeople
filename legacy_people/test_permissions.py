"""Authorization coverage for sensitive dashboard HTML and AJAX responses."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from .models import Person

User = get_user_model()


class DashboardPermissionTests(TestCase):
    dashboard_queries = (
        "", "?stat_ajax=1&type=all", "?stat_ajax=1&type=no_gc", "?stat_ajax=1&type=wants_chat",
        "?feeling_ajax=1&feeling=1", "?ajax=1&page=1",
    )

    @classmethod
    def setUpTestData(cls):
        permission = Permission.objects.get(
            codename="view_person", content_type__app_label="legacy_people", content_type__model="person",
        )
        cls.staff = User.objects.create_user(username="staff", password="test-password", is_staff=True)
        cls.staff.user_permissions.add(permission)
        cls.regular = User.objects.create_user(username="regular", password="test-password")
        # A view permission alone must not grant access to the administrative area.
        cls.regular.user_permissions.add(permission)
        cls.unprivileged_staff = User.objects.create_user(
            username="unprivileged", password="test-password", is_staff=True,
        )
        cls.inactive_staff = User.objects.create_user(
            username="inactive", password="test-password", is_staff=True, is_active=False,
        )
        cls.inactive_staff.user_permissions.add(permission)
        cls.superuser = User.objects.create_superuser(username="superuser", password="test-password")
        Person.objects.create(
            name="Confidential Person", email="private@example.com", whatsapp="+5511999999999",
            time_lagoinha="menos_6_meses", feeling=1, prayer_request="Confidential prayer", wants_chat=True,
        )

    def test_anonymous_requests_redirect_to_login(self):
        for query in self.dashboard_queries:
            with self.subTest(query=query):
                response = self.client.get(reverse("legacy_people:dashboard") + query)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("legacy_people:login"), response.url)

    def test_users_without_staff_status_or_permission_are_forbidden(self):
        for user in (self.regular, self.unprivileged_staff):
            self.client.force_login(user)
            for query in self.dashboard_queries:
                with self.subTest(user=user.username, query=query):
                    response = self.client.get(reverse("legacy_people:dashboard") + query)
                    self.assertEqual(response.status_code, 403)
                    self.assertNotContains(response, "Confidential Person", status_code=403)
                    self.assertNotContains(response, "private@example.com", status_code=403)
                    self.assertNotContains(response, "Confidential prayer", status_code=403)

    def test_authorized_staff_and_superusers_can_read_all_responses(self):
        for user in (self.staff, self.superuser):
            self.client.force_login(user)
            for query in self.dashboard_queries:
                with self.subTest(user=user.username, query=query):
                    response = self.client.get(reverse("legacy_people:dashboard") + query)
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, "Confidential Person")

    def test_administrative_login_rejects_unauthorized_users(self):
        for user in (self.regular, self.unprivileged_staff, self.inactive_staff):
            with self.subTest(user=user.username):
                response = self.client.post(reverse("legacy_people:login"), {
                    "username": user.username, "password": "test-password",
                })
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_authenticated_unauthorized_user_is_not_redirected_to_dashboard(self):
        self.client.force_login(self.regular)
        response = self.client.get(reverse("legacy_people:login"))
        self.assertRedirects(response, reverse("legacy_people:landing"))

    def test_navigation_only_links_to_dashboard_for_authorized_users(self):
        for user, expected in ((self.regular, False), (self.unprivileged_staff, False), (self.staff, True)):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(reverse("legacy_people:landing"))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(f'href="{reverse("legacy_people:dashboard")}"' in response.content.decode(), expected)

    def test_permission_revocation_takes_effect_in_existing_session(self):
        self.client.force_login(self.staff)
        url = reverse("legacy_people:dashboard") + "?stat_ajax=1&type=all"
        self.assertEqual(self.client.get(url).status_code, 200)
        self.staff.user_permissions.clear()
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_staff_status_revocation_takes_effect_in_existing_session(self):
        self.client.force_login(self.staff)
        self.staff.is_staff = False
        self.staff.save(update_fields=["is_staff"])
        self.assertEqual(self.client.get(reverse("legacy_people:dashboard")).status_code, 403)
