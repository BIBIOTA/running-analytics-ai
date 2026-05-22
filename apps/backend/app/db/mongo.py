from __future__ import annotations

import asyncio
from typing import Any, Callable

from app.core.config import Settings


class MongoDatabase:
    def __init__(self, database: Any | None = None, client: Any | None = None) -> None:
        self._client = client
        self._database = database

    async def connect(
        self,
        settings: Settings,
        client_factory: Callable[[str], Any] | None = None,
    ) -> None:
        if self._database is not None:
            return

        if client_factory is None:
            from motor.motor_asyncio import AsyncIOMotorClient

            client_factory = AsyncIOMotorClient

        self._client = client_factory(settings.mongodb_uri)
        self._database = self._client[settings.mongodb_database]
        await self.create_indexes()

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
        self._client = None
        self._database = None

    @property
    def database(self) -> Any:
        if self._database is None:
            raise RuntimeError("MongoDB is not connected")
        return self._database

    @property
    def users(self) -> Any:
        return self.database["users"]

    @property
    def conversations(self) -> Any:
        return self.database["conversations"]

    @property
    def llm_logs(self) -> Any:
        return self.database["llm_logs"]

    async def create_indexes(self) -> None:
        await asyncio.gather(
            self.users.create_index([("strava_athlete_id", 1)], unique=True),
            self.conversations.create_index(
                [("user_id", 1), ("activity_id", 1), ("updated_at", -1)]
            ),
            self.llm_logs.create_index([("user_id", 1), ("created_at", -1)]),
        )


mongo = MongoDatabase()
