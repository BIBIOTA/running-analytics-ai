from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, encrypt_token
from app.db.mongo import mongo
from app.models.common import utc_now
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

STRAVA_AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_SCOPE = "activity:read_all,profile:read_all"


class MeResponse(BaseModel):
    strava_athlete_id: int
    display_name: str
    profile_image_url: str | None = None


class StravaOAuthClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def exchange_code(self, code: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                STRAVA_TOKEN_URL,
                data={
                    "client_id": self.settings.strava_client_id,
                    "client_secret": self.settings.strava_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )
        response.raise_for_status()
        return response.json()


@router.get("/strava")
async def strava_login(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> RedirectResponse:
    query = urlencode(
        {
            "client_id": settings.strava_client_id,
            "redirect_uri": str(request.url_for("strava_callback")),
            "response_type": "code",
            "scope": STRAVA_SCOPE,
        }
    )
    return RedirectResponse(f"{STRAVA_AUTHORIZE_URL}?{query}", status_code=302)


@router.get("/strava/callback", name="strava_callback")
async def strava_callback(
    settings: Annotated[Settings, Depends(get_settings)],
    code: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    if error is not None:
        return RedirectResponse(f"{settings.frontend_url}/login?error={error}", status_code=302)
    if code is None:
        raise HTTPException(status_code=400, detail="Missing OAuth code")

    token_response = await StravaOAuthClient(settings).exchange_code(code)
    user_id = await upsert_strava_user(token_response, settings=settings)
    jwt_token = create_access_token(user_id, settings=settings)
    return RedirectResponse(f"{settings.frontend_url}/callback?token={jwt_token}", status_code=302)


@router.get("/me", response_model=MeResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> MeResponse:
    return MeResponse(
        strava_athlete_id=current_user.strava_athlete_id,
        display_name=current_user.display_name,
        profile_image_url=current_user.profile_image_url,
    )


async def upsert_strava_user(token_response: dict[str, Any], *, settings: Settings) -> str:
    athlete = token_response["athlete"]
    strava_athlete_id = int(athlete["id"])
    now = utc_now()
    display_name = _athlete_display_name(athlete)
    expires_at = datetime.fromtimestamp(
        int(token_response["expires_at"]),
        tz=timezone.utc,  # noqa: UP017 - local test runner is Python 3.10.
    )

    await mongo.users.update_one(
        {"strava_athlete_id": strava_athlete_id},
        {
            "$setOnInsert": {"created_at": now},
            "$set": {
                "strava_athlete_id": strava_athlete_id,
                "display_name": display_name,
                "profile_image_url": athlete.get("profile") or athlete.get("profile_medium"),
                "strava_access_token": encrypt_token(
                    token_response["access_token"],
                    settings=settings,
                ),
                "strava_refresh_token": encrypt_token(
                    token_response["refresh_token"],
                    settings=settings,
                ),
                "strava_token_expires_at": expires_at,
                "updated_at": now,
            },
        },
        upsert=True,
    )
    user = await mongo.users.find_one({"strava_athlete_id": strava_athlete_id})
    if user is None or "_id" not in user:
        raise RuntimeError("Failed to load upserted user")
    return str(user["_id"])


def _athlete_display_name(athlete: dict[str, Any]) -> str:
    full_name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()
    return full_name or str(athlete["id"])
