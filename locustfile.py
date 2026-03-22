import random
from datetime import datetime, timedelta

from locust import HttpUser, task, between


class UrlShortenerUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        email = f"perf_user_{random.randint(1, 1_000_000)}@example.com"
        password = "pass1234"

        reg_payload = {"email": email, "password": password}
        self.client.post("/auth/register", json=reg_payload)

        login_form = {"username": email, "password": password}
        resp = self.client.post("/auth/login", data=login_form)
        data = resp.json()
        token = data.get("access_token")
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

        self.short_codes = []

    @task(3)
    def create_link(self):
        expires_at = (datetime.utcnow() + timedelta(days=1)).isoformat()
        payload = {
            "original_url": "https://example.com",
            "expires_at": expires_at,
            "custom_alias": None,
        }
        resp = self.client.post(
            "/links/shorten",
            json=payload,
            headers=self.headers,
        )
        if resp.status_code == 201:
            data = resp.json()
            code = data.get("short_code")
            if code:
                self.short_codes.append(code)

    @task(5)
    def redirect_random_link(self):
        if not self.short_codes:
            return
        code = random.choice(self.short_codes)
        self.client.get(f"/{code}", allow_redirects=False)

    @task(1)
    def get_stats_for_random_link(self):
        if not self.short_codes:
            return
        code = random.choice(self.short_codes)
        self.client.get(f"/links/{code}/stats", headers=self.headers)
