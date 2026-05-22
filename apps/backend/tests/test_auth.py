from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


TEST_ENV = {
    "STRAVA_CLIENT_ID": "client-id",
    "STRAVA_CLIENT_SECRET": "client-secret",
    "GEMINI_API_KEY": "gemini-key",
    "MONGODB_URI": "mongodb://mongodb:27017/running_analytics",
    "JWT_SECRET": "jwt-secret",
    "ENCRYPTION_KEY": "a" * 32,
    "FRONTEND_URL": "http://frontend.test",
    "BACKEND_URL": "http://api.test",
}
UTC = getattr(__import__("datetime"), "UTC", timezone.__dict__["utc"])


class FakeUsersCollection:
    def __init__(self) -> None:
        self.documents: dict[int, dict[str, object]] = {}
        self.last_filter: dict[str, object] | None = None
        self.last_update: dict[str, object] | None = None

    async def find_one_and_update(
        self,
        filter_query: dict[str, object],
        update: dict[str, object],
        *,
        upsert: bool,
        return_document: object,
    ) -> dict[str, object]:
        self.last_filter = filter_query
        self.last_update = update
        athlete_id = int(filter_query["strava_athlete_id"])
        existing = self.documents.get(athlete_id, {})
        set_on_insert = update.get("$setOnInsert", {})
        set_values = update.get("$set", {})
        document = {
            **set_on_insert,  # type: ignore[arg-type]
            **existing,
            **set_values,  # type: ignore[arg-type]
            "_id": existing.get("_id", f"user-{athlete_id}"),
            "strava_athlete_id": athlete_id,
        }
        self.documents[athlete_id] = document
        return document

    async def find_one(self, filter_query: dict[str, object]) -> dict[str, object] | None:
        if "_id" in filter_query:
            expected_id = filter_query["_id"]
            return next(
                (
                    document
                    for document in self.documents.values()
                    if document["_id"] == expected_id
                ),
                None,
            )
        if "strava_athlete_id" in filter_query:
            return self.documents.get(int(filter_query["strava_athlete_id"]))
        return None


class FakeDatabase:
    def __init__(self, users: FakeUsersCollection) -> None:
        self.users = users

    def __getitem__(self, name: str) -> FakeUsersCollection:
        if name != "users":
            raise KeyError(name)
        return self.users


class StravaAuthTests(TestCase):
    def setUp(self) -> None:
        self.users = FakeUsersCollection()

    def tearDown(self) -> None:
        from app.core.config import get_settings
        from app.db.mongo import mongo

        get_settings.cache_clear()
        mongo._database = None
        mongo._client = None

    def make_client(self) -> TestClient:
        from app.core.config import get_settings
        from app.db.mongo import mongo
        from app.main import create_app

        get_settings.cache_clear()
        mongo._database = FakeDatabase(self.users)
        return TestClient(create_app())

    def test_strava_auth_redirects_to_strava_authorize_url(self) -> None:
        with patch.dict("os.environ", TEST_ENV):
            client = self.make_client()
            response = client.get("/auth/strava", follow_redirects=False)

        self.assertEqual(response.status_code, 307)
        location = response.headers["location"]
        parsed = urlparse(location)
        query = parse_qs(parsed.query)

        self.assertEqual(
            f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
            "https://www.strava.com/oauth/authorize",
        )
        self.assertEqual(query["client_id"], ["client-id"])
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["redirect_uri"], ["http://api.test/auth/strava/callback"])
        self.assertEqual(query["approval_prompt"], ["auto"])
        self.assertEqual(query["scope"], ["activity:read_all,profile:read_all"])

    def test_strava_callback_exchanges_code_upserts_user_and_redirects_with_jwt(self) -> None:
        token_response = {
            "access_token": "plain-access-token",
            "refresh_token": "plain-refresh-token",
            "expires_at": 1_800_000_000,
            "athlete": {
                "id": 123,
                "firstname": "Ada",
                "lastname": "Runner",
                "profile": "https://example.test/profile.jpg",
            },
        }

        async def fake_exchange_code(code: str) -> dict[str, object]:
            self.assertEqual(code, "valid-code")
            return token_response

        with (
            patch.dict("os.environ", TEST_ENV),
            patch("app.api.auth.exchange_code", fake_exchange_code),
        ):
            client = self.make_client()
            response = client.get("/auth/strava/callback?code=valid-code", follow_redirects=False)

        self.assertEqual(response.status_code, 307)
        location = response.headers["location"]
        parsed = urlparse(location)
        query = parse_qs(parsed.query)
        self.assertEqual(
            f"{parsed.scheme}://{parsed.netloc}{parsed.path}", "http://frontend.test/callback"
        )
        self.assertIn("token", query)

        stored_user = self.users.documents[123]
        self.assertEqual(stored_user["display_name"], "Ada Runner")
        self.assertEqual(stored_user["profile_image_url"], "https://example.test/profile.jpg")
        self.assertEqual(
            stored_user["strava_token_expires_at"],
            datetime.fromtimestamp(1_800_000_000, UTC),
        )
        self.assertNotEqual(stored_user["strava_access_token"], "plain-access-token")
        self.assertNotEqual(stored_user["strava_refresh_token"], "plain-refresh-token")

    def test_strava_callback_redirects_to_login_when_access_denied(self) -> None:
        with patch.dict("os.environ", TEST_ENV):
            client = self.make_client()
            response = client.get(
                "/auth/strava/callback?error=access_denied",
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 307)
        self.assertEqual(
            response.headers["location"], "http://frontend.test/login?error=access_denied"
        )

    def test_auth_me_returns_current_user_from_bearer_token(self) -> None:
        self.users.documents[123] = {
            "_id": "user-123",
            "strava_athlete_id": 123,
            "display_name": "Ada Runner",
            "profile_image_url": "https://example.test/profile.jpg",
            "strava_access_token": "encrypted-access",
            "strava_refresh_token": "encrypted-refresh",
            "strava_token_expires_at": datetime.fromtimestamp(1_800_000_000, UTC),
        }

        with patch.dict("os.environ", TEST_ENV):
            from app.core.security import create_access_token

            token = create_access_token("user-123")
            client = self.make_client()
            response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "strava_athlete_id": 123,
                "display_name": "Ada Runner",
                "profile_image_url": "https://example.test/profile.jpg",
            },
        )
