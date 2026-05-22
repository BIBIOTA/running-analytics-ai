from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from httpx import ASGITransport, AsyncClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


TEST_ENV = {
    "STRAVA_CLIENT_ID": "client-id",
    "STRAVA_CLIENT_SECRET": "client-secret",
    "GEMINI_API_KEY": "gemini-key",
    "MONGODB_URI": "mongodb://mongodb:27017/running_analytics",
    "JWT_SECRET": "jwt-secret",
    "ENCRYPTION_KEY": "0123456789abcdef0123456789abcdef",
    "BACKEND_URL": "http://testserver",
    "FRONTEND_URL": "http://localhost:3000",
}


class AuthSecurityTests(TestCase):
    def test_jwt_round_trip_preserves_subject(self) -> None:
        from app.core.config import Settings
        from app.core.security import create_access_token, decode_access_token

        settings = Settings(**{key.lower(): value for key, value in TEST_ENV.items()})

        token = create_access_token("user-123", settings=settings)

        payload = decode_access_token(token, settings=settings)
        self.assertEqual(payload["sub"], "user-123")
        self.assertEqual(payload["type"], "access")
        self.assertIn("exp", payload)

    def test_strava_tokens_are_encrypted_and_decryptable(self) -> None:
        from app.core.config import Settings
        from app.core.security import decrypt_token, encrypt_token

        settings = Settings(**{key.lower(): value for key, value in TEST_ENV.items()})

        encrypted = encrypt_token("plain-strava-token", settings=settings)

        self.assertNotEqual(encrypted, "plain-strava-token")
        self.assertEqual(decrypt_token(encrypted, settings=settings), "plain-strava-token")


class FakeUsersCollection:
    def __init__(self) -> None:
        self.document: dict[str, Any] | None = None

    async def create_index(self, *args: object, **kwargs: object) -> str:
        return "index"

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        if self.document is None:
            return None
        if "_id" in query and self.document["_id"] == query["_id"]:
            return self.document
        if (
            "strava_athlete_id" in query
            and self.document["strava_athlete_id"] == query["strava_athlete_id"]
        ):
            return self.document
        return None

    async def update_one(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
    ) -> Any:
        set_on_insert = update.get("$setOnInsert", {})
        set_values = update.get("$set", {})
        if self.document is None:
            self.document = {"_id": "user-123", **set_on_insert, **set_values}
        else:
            self.document.update(set_values)

        class Result:
            upserted_id = "user-123"

        return Result()


class FakeDatabase:
    def __init__(self) -> None:
        self.users = FakeUsersCollection()

    def __getitem__(self, name: str) -> Any:
        if name == "users":
            return self.users
        raise AssertionError(f"unexpected collection: {name}")


class AuthEndpointTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.env_patcher = patch.dict("os.environ", TEST_ENV)
        self.env_patcher.start()

        from app.core.config import get_settings

        get_settings.cache_clear()
        from app.main import create_app

        self.app = create_app()
        get_settings.cache_clear()

        from app.db.mongo import mongo

        self.fake_db = FakeDatabase()
        self.original_database = mongo._database
        self.original_client = mongo._client
        mongo._database = self.fake_db
        mongo._client = None

    async def asyncTearDown(self) -> None:
        from app.core.config import get_settings
        from app.db.mongo import mongo

        mongo._database = self.original_database
        mongo._client = self.original_client
        get_settings.cache_clear()
        self.env_patcher.stop()

    async def test_strava_login_redirect_includes_required_oauth_parameters(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url="http://testserver",
            follow_redirects=False,
        ) as client:
            response = await client.get("/auth/strava")

        self.assertEqual(response.status_code, 302)
        location = response.headers["location"]
        parsed = urlparse(location)
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "www.strava.com")
        self.assertEqual(parsed.path, "/oauth/authorize")
        self.assertEqual(query["client_id"], ["client-id"])
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["scope"], ["activity:read_all,profile:read_all"])
        self.assertEqual(
            query["redirect_uri"],
            ["http://testserver/auth/strava/callback"],
        )

    async def test_callback_upserts_encrypted_tokens_and_redirects_with_jwt(self) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=6)  # noqa: UP017
        strava_response = {
            "access_token": "strava-access",
            "refresh_token": "strava-refresh",
            "expires_at": int(expires_at.timestamp()),
            "athlete": {
                "id": 987,
                "firstname": "Ada",
                "lastname": "Runner",
                "profile": "https://example.test/ada.jpg",
            },
        }

        with patch("app.api.auth.StravaOAuthClient.exchange_code", return_value=strava_response):
            async with AsyncClient(
                transport=ASGITransport(app=self.app),
                base_url="http://testserver",
                follow_redirects=False,
            ) as client:
                response = await client.get("/auth/strava/callback?code=oauth-code")

        self.assertEqual(response.status_code, 302)
        redirect = urlparse(response.headers["location"])
        self.assertEqual(
            f"{redirect.scheme}://{redirect.netloc}{redirect.path}",
            "http://localhost:3000/callback",
        )
        token = parse_qs(redirect.query)["token"][0]

        from app.core.config import Settings
        from app.core.security import decode_access_token

        payload = decode_access_token(
            token,
            settings=Settings(**{key.lower(): value for key, value in TEST_ENV.items()}),
        )
        self.assertEqual(payload["sub"], "user-123")

        stored_user = self.fake_db.users.document
        assert stored_user is not None
        self.assertEqual(stored_user["strava_athlete_id"], 987)
        self.assertEqual(stored_user["display_name"], "Ada Runner")
        self.assertNotEqual(stored_user["strava_access_token"], "strava-access")
        self.assertNotEqual(stored_user["strava_refresh_token"], "strava-refresh")

    async def test_callback_access_denied_redirects_to_login_error(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url="http://testserver",
            follow_redirects=False,
        ) as client:
            response = await client.get("/auth/strava/callback?error=access_denied")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["location"],
            "http://localhost:3000/login?error=access_denied",
        )

    async def test_me_returns_current_user_for_valid_bearer_token(self) -> None:
        from app.core.config import Settings
        from app.core.security import create_access_token

        self.fake_db.users.document = {
            "_id": "user-123",
            "strava_athlete_id": 987,
            "display_name": "Ada Runner",
            "profile_image_url": "https://example.test/ada.jpg",
            "strava_access_token": "encrypted-access",
            "strava_refresh_token": "encrypted-refresh",
            "strava_token_expires_at": datetime.now(timezone.utc)  # noqa: UP017
            + timedelta(hours=1),
            "created_at": datetime.now(timezone.utc),  # noqa: UP017
            "updated_at": datetime.now(timezone.utc),  # noqa: UP017
        }
        token = create_access_token(
            "user-123",
            settings=Settings(**{key.lower(): value for key, value in TEST_ENV.items()}),
        )

        async with AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url="http://testserver",
        ) as client:
            response = await client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "strava_athlete_id": 987,
                "display_name": "Ada Runner",
                "profile_image_url": "https://example.test/ada.jpg",
            },
        )

    async def test_me_rejects_invalid_token(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url="http://testserver",
        ) as client:
            response = await client.get(
                "/auth/me",
                headers={"Authorization": "Bearer invalid-token"},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid or expired token"})
