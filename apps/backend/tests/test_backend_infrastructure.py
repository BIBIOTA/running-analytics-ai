from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, TestCase


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


class ConfigTests(TestCase):
    def test_settings_read_required_environment_and_frontend_default(self) -> None:
        from app.core.config import Settings

        settings = Settings(
            strava_client_id="client-id",
            strava_client_secret="client-secret",
            gemini_api_key="gemini-key",
            mongodb_uri="mongodb://mongodb:27017/running_analytics",
            jwt_secret="jwt-secret",
            encryption_key="a" * 32,
        )

        self.assertEqual(settings.strava_client_id, "client-id")
        self.assertEqual(settings.frontend_url, "http://localhost:3000")
        self.assertEqual(settings.mongodb_database, "running_analytics")
        self.assertEqual(settings.gemini_model, "gemini-3.1-pro-preview")


class AppTests(TestCase):
    def test_create_app_configures_cors_and_health_route(self) -> None:
        from fastapi.middleware.cors import CORSMiddleware

        os.environ.update(
            {
                "STRAVA_CLIENT_ID": "client-id",
                "STRAVA_CLIENT_SECRET": "client-secret",
                "GEMINI_API_KEY": "gemini-key",
                "MONGODB_URI": "mongodb://mongodb:27017/running_analytics",
                "JWT_SECRET": "jwt-secret",
                "ENCRYPTION_KEY": "a" * 32,
            }
        )
        from app.core.config import get_settings

        get_settings.cache_clear()
        from app.main import create_app

        app = create_app()

        route_paths = {route.path for route in app.routes}
        self.assertIn("/health", route_paths)

        cors = [
            middleware
            for middleware in app.user_middleware
            if middleware.cls is CORSMiddleware
        ]
        self.assertEqual(len(cors), 1)
        self.assertEqual(cors[0].kwargs["allow_origins"], ["http://localhost:3000"])


class FakeCollection:
    def __init__(self) -> None:
        self.indexes: list[tuple[tuple[object, ...], dict[str, object]]] = []

    async def create_index(self, *args: object, **kwargs: object) -> str:
        self.indexes.append((args, kwargs))
        return "index"


class FakeDatabase:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        self.collections.setdefault(name, FakeCollection())
        return self.collections[name]


class MongoTests(IsolatedAsyncioTestCase):
    async def test_database_accessors_and_indexes(self) -> None:
        from app.db.mongo import MongoDatabase

        db = FakeDatabase()
        mongo = MongoDatabase(database=db)

        self.assertIs(mongo.users, db["users"])
        self.assertIs(mongo.conversations, db["conversations"])
        self.assertIs(mongo.llm_logs, db["llm_logs"])

        await mongo.create_indexes()

        self.assertIn(
            (([("strava_athlete_id", 1)],), {"unique": True}),
            db["users"].indexes,
        )
        self.assertIn(
            (([("user_id", 1), ("activity_id", 1), ("updated_at", -1)],), {}),
            db["conversations"].indexes,
        )
        self.assertIn(
            (([("user_id", 1), ("created_at", -1)],), {}),
            db["llm_logs"].indexes,
        )


class ModelTests(TestCase):
    def test_user_conversation_and_llm_log_models_serialize(self) -> None:
        from app.models.conversation import Conversation, Message, MessageRole
        from app.models.llm_log import LlmLog, LlmLogStatus
        from app.models.user import User

        now = datetime(2026, 5, 22, 9, 0, tzinfo=timezone.utc)
        user = User(
            id="user-1",
            strava_athlete_id=123,
            display_name="Runner",
            profile_image_url="https://example.test/avatar.jpg",
            strava_access_token="encrypted-access",
            strava_refresh_token="encrypted-refresh",
            strava_token_expires_at=now,
            created_at=now,
            updated_at=now,
        )
        conversation = Conversation(
            id="conversation-1",
            user_id=user.id,
            activity_id=None,
            messages=[
                Message(role=MessageRole.USER, content="分析我近一個月的跑步活動", created_at=now)
            ],
            created_at=now,
            updated_at=now,
        )
        log = LlmLog(
            request_id="request-1",
            user_id=user.id,
            conversation_id=conversation.id,
            activity_ids=[],
            provider_name="google",
            model_name="gemini-3.1-pro-preview",
            prompt_version="v1.0.0",
            input_tokens=10,
            output_tokens=20,
            total_tokens=30,
            latency_ms=1500,
            status=LlmLogStatus.SUCCESS,
            created_at=now,
        )

        self.assertEqual(user.model_dump(by_alias=True)["_id"], "user-1")
        self.assertIsNone(conversation.activity_id)
        self.assertEqual(conversation.messages[0].role, MessageRole.USER)
        self.assertEqual(log.total_tokens, 30)
        self.assertEqual(log.status, LlmLogStatus.SUCCESS)
