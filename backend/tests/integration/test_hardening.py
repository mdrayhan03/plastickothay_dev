"""B7 hardening — throttling actually enforces, and the SPA catch-all serves."""

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="  # noqa: E501
PNG = f"data:image/png;base64,{_B64}"


def _submit(client):
    return client.post("/api/posts/", {
        "severity": 3, "lat": 23.8, "lon": 90.4, "photo": PNG,
        "name": "A", "email": "a@e.com", "phone": "+880",
    }, format="json")


class TestThrottling:
    def test_anonymous_submission_is_rate_limited(self):
        """anon_post_submit is 5/hour. The 6th within the window is 429."""
        client = APIClient()
        codes = [_submit(client).status_code for _ in range(6)]
        assert codes[:5] == [201, 201, 201, 201, 201]
        assert codes[5] == 429

    def test_feedback_is_rate_limited(self):
        client = APIClient()
        codes = [
            client.post("/api/feedback/", {"rating": 5}, format="json").status_code
            for _ in range(6)
        ]
        assert codes[5] == 429


class TestSPACatchAll:
    def test_unknown_route_returns_spa_not_404(self):
        """Client-side routes must fall through to the SPA, not 404."""
        resp = APIClient().get("/dashboard/some/deep/link")
        assert resp.status_code == 200
        assert b"PlasticKothay" in resp.content

    def test_api_routes_are_not_swallowed_by_the_catch_all(self):
        # A real (unknown) API path still returns a JSON 404, not the SPA HTML.
        resp = APIClient().get("/api/posts/999999/")
        assert resp.status_code == 404
        assert resp["content-type"].startswith("application/json")
