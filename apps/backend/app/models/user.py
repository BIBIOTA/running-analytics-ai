from datetime import datetime

from pydantic import Field

from app.models.common import MongoModel, utc_now


class User(MongoModel):
    strava_athlete_id: int
    display_name: str
    profile_image_url: str | None = None
    strava_access_token: str
    strava_refresh_token: str
    strava_token_expires_at: datetime
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
