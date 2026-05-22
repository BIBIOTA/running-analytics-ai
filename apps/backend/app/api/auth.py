from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, encrypt_token
from app.db.mongo import mongo
from app.models.user import User
from app.services.strava import exchange_code

UTC = getattr(__import__("datetime"), "UTC", timezone.__dict__["utc"])
current_user_dependency = Depends(get_current_user)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/strava")
async def redirect_to_strava() -> RedirectResponse:
    settings = get_settings()
    callback_url = settings.backend_url.rstrip("/") + "/auth/strava/callback"
    query = urlencode(
        {
            "client_id": settings.strava_client_id,
            "response_type": "code",
            "redirect_uri": callback_url,
            "approval_prompt": "auto",
            "scope": "activity:read_all,profile:read_all",
        }
    )
    return RedirectResponse(f"https://www.strava.com/oauth/authorize?{query}")


@router.get("/strava/callback")
async def strava_callback(
    code: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    settings = get_settings()
    if error:
        query = urlencode({"error": error})
        return RedirectResponse(f"{settings.frontend_url.rstrip('/')}/login?{query}")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code")

    token_response = await exchange_code(code)
    athlete = token_response["athlete"]
    display_name = _athlete_display_name(athlete)
    now = datetime.now(UTC)
    user_document = await mongo.users.find_one_and_update(
        {"strava_athlete_id": athlete["id"]},
        {
            "$set": {
                "display_name": display_name,
                "profile_image_url": athlete.get("profile"),
                "strava_access_token": encrypt_token(str(token_response["access_token"])),
                "strava_refresh_token": encrypt_token(str(token_response["refresh_token"])),
                "strava_token_expires_at": datetime.fromtimestamp(
                    int(token_response["expires_at"]),
                    UTC,
                ),
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
        return_document=True,
    )
    token = create_access_token(str(user_document["_id"]))
    query = urlencode({"token": token})
    return RedirectResponse(f"{settings.frontend_url.rstrip('/')}/callback?{query}")


@router.get("/me")
async def get_me(current_user: User = current_user_dependency) -> dict[str, object]:
    return {
        "strava_athlete_id": current_user.strava_athlete_id,
        "display_name": current_user.display_name,
        "profile_image_url": current_user.profile_image_url,
    }


def _athlete_display_name(athlete: dict[str, object]) -> str:
    first_name = str(athlete.get("firstname") or "").strip()
    last_name = str(athlete.get("lastname") or "").strip()
    display_name = f"{first_name} {last_name}".strip()
    return display_name or f"Strava Athlete {athlete['id']}"
