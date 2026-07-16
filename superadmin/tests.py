from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from superadmin import views


class AdminDashboardAccessTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _build_request(self):
        request = self.factory.get(reverse("superadmin:dashboard"))
        request.session = {"user_id": "123"}
        return request

    @patch("superadmin.views.wishes", return_value="Morning")
    @patch("superadmin.views.Post.objects")
    @patch("superadmin.views.get_user")
    def test_dashboard_redirects_regular_user_to_unauthorized(self, fake_get_user, fake_objects, fake_wishes):
        fake_get_user.return_value = SimpleNamespace(
            user_type=3,
            first_name="Jane",
            last_name="Doe",
            username="jane",
            is_active=True,
        )
        fake_objects.return_value.count.return_value = 0
        fake_objects.return_value.to_json.return_value = "[]"

        response = views.dashboard(self._build_request())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("superadmin:unauthorized"))

    @patch("superadmin.views.wishes", return_value="Morning")
    @patch("superadmin.views.Post.objects")
    @patch("superadmin.views.get_user")
    def test_dashboard_renders_for_admin_user(self, fake_get_user, fake_objects, fake_wishes):
        fake_get_user.return_value = SimpleNamespace(
            user_type=2,
            first_name="Admin",
            last_name="User",
            username="admin",
            is_active=True,
        )
        fake_objects.return_value.count.return_value = 0
        fake_objects.return_value.to_json.return_value = "[]"

        response = views.dashboard(self._build_request())

        self.assertEqual(response.status_code, 200)
