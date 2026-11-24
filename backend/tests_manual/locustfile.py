import base64
import io
import os
import random
import logging
from locust import HttpUser, between, task

logger = logging.getLogger(__name__)

# 1x1 valid PNG (68 bytes) so report creation tests real multipart uploads without hitting bandwidth limits
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
)


class PlasticKothayUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.email = os.getenv("LOCUST_EMAIL", "test@example.com")
        self.password = os.getenv("LOCUST_PASSWORD", "testpassword123")
        self.user = None
        self.headers = {}
        self.post_ids = []
        self.login()

    def login(self):
        with self.client.post(
            "/api/auth/login/",
            json={"username": self.email, "password": self.password},
            name="/api/auth/login/",
            catch_response=True,
        ) as res:
            if res.status_code == 200:
                data = res.json()
                self.user = data.get("user")
                # Supports both Bearer JWT responses and cookie-based sessions automatically
                token = data.get("access") or data.get("access_token") or data.get("token")
                if token:
                    self.headers["Authorization"] = f"Bearer {token}"
                res.success()
            else:
                res.failure(f"Login failed ({res.status_code}): {res.text[:120]}")

    @task(5)
    def list_posts(self):
        with self.client.get(
            "/api/posts/",
            headers=self.headers,
            name="/api/posts/ [GET]",
            catch_response=True,
        ) as res:
            if res.status_code == 200:
                data = res.json()
                items = data.get("results", data) if isinstance(data, dict) else data
                if isinstance(items, list) and items:
                    self.post_ids = [p["id"] for p in items if isinstance(p, dict) and "id" in p]
                res.success()
            else:
                res.failure(f"List posts failed: {res.status_code}")

    @task(3)
    def map_posts(self):
        self.client.get(
            "/api/map/posts/",
            headers=self.headers,
            name="/api/map/posts/",
        )

    @task(4)
    def check_post_detail(self):
        if not self.post_ids:
            return
        post_id = random.choice(self.post_ids)
        self.client.get(
            f"/api/posts/{post_id}/",
            headers=self.headers,
            name="/api/posts/[id]/",
        )

    @task(2)
    def toggle_like(self):
        if not self.post_ids:
            return
        post_id = random.choice(self.post_ids)

        # 1. Like the post (POST)
        with self.client.post(
            f"/api/posts/{post_id}/like/",
            headers=self.headers,
            name="/api/posts/[id]/like/ [POST]",
            catch_response=True,
        ) as res:
            if res.status_code in (200, 201, 409):
                res.success()
            else:
                res.failure(f"Like failed ({res.status_code}): {res.text[:120]}")

        # 2. Unlike the post (DELETE) so the state stays clean for future iterations
        with self.client.delete(
            f"/api/posts/{post_id}/like/",
            headers=self.headers,
            name="/api/posts/[id]/like/ [DELETE]",
            catch_response=True,
        ) as res:
            if res.status_code in (200, 204, 404):
                res.success()
            else:
                res.failure(f"Unlike failed ({res.status_code}): {res.text[:120]}")

    @task(1)
    def create_report_post(self):
        # Adjust field names ("image", "lat", "lon", "severity", "description", "place_name")
        # if your ReportListCreateView serializer expects slightly different keys
        lat = round(random.uniform(23.72, 23.86), 6)
        lon = round(random.uniform(90.36, 90.44), 6)

        byte_stream = io.BytesIO(TINY_PNG)
        png_string = base64.b64encode(byte_stream.getvalue()).decode("utf-8")
        data_uri = f"data:image/png;base64,{png_string}"

        data = {
            "severity": random.choice([1, 2, 3, 4, 5]),
            "lat": str(lat),
            "lon": str(lon),
            "photo": data_uri,
            "place_name": "Badda, Dhaka",
            "description": "Locust load test report entry.",
            "name": f"{self.user.get("first_name")} {self.user.get("last_name")}",
            "email": self.user.get("email"),
            "phone": self.user.get("phone")
        }
        with self.client.post(
            "/api/posts/",
            data=data,
            headers=self.headers,
            name="/api/posts/ [POST]",
            catch_response=True,
        ) as res:
            if res.status_code in (200, 201):
                created = res.json()
                if isinstance(created, dict) and "id" in created:
                    self.post_ids.append(created["id"])
                res.success()
            else:
                res.failure(f"Create report failed ({res.status_code}): {res.text[:150]}")