import re
from fastapi import Cookie, Depends, HTTPException, status, Response
from typing import Annotated
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.util.security import hash_token, new_session_token
from app.db import get_db
from app.models import User, UserSession
from app.config import settings

COOKIE_NAME = "session"
DISPLAY_NAME_RE = re.compile(r"^[\w .\-'!?~★☆]{1,32}$")

def start_session(db: Session, user: User, response: Response) -> None:
    token = new_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.session_days)
    db.add(UserSession(user_id=user.id, token_hash=hash_token(token), expires_at=expires_at))
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.session_days * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure
    )

def get_current_user(
        session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
        db: Session = Depends(get_db),
) -> User:
    if not session_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in!")

    user = db.scalar(
        select(User)
        .join(UserSession)
        .where(
            UserSession.token_hash == hash_token(session_token),
            UserSession.expires_at > func.now(),
            User.is_active.is_(True),
        )
        .options(selectinload(User.ratings))
    )

    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or invalid")

    return user

CurrentUser = Annotated[User, Depends(get_current_user)]