from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.db.mongo import mongo
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)
bearer_credentials_dependency = Depends(bearer_scheme)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = bearer_credentials_dependency,
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    try:
        user_id = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    document = await mongo.users.find_one({"_id": user_id})
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return User.model_validate(document)
