from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
import uuid
import re
import unicodedata
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.security import (
    hash_password,
    hash_token,
    new_session_token,
    verify_password,
)

from app.config import settings
from app.db import get_db
from app.models import User, UserSession

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "session"
DISPLAY_NAME_RE = re.compile(r"^[\w .\-'!?~★☆]{1,32}$")

# SCHEMAS

class RegisterIn(BaseModel):
    username: str = Field(pattern=r"^[A-Za-z0-9_]{3,20}$")
    email: EmailStr
    display_name: str | None = None
    password: str = Field(min_length=8, max_length=128)

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, value: str | None) -> str:
        if value is None:
            return None
        value = unicodedata.normalize("NFC", value)
        value = " ".join(value.split())

        if not value:
            return None

        if not DISPLAY_NAME_RE.fullmatch(value):
            raise ValueError("Display name can use letters, numbers, spaces and - ' ! ? ~ ★ ☆ (1–32 characters)")
        return value

    @model_validator(mode="after")
    def default_display_name(self):
        if self.display_name is None:
            self.display_name = self.username
        return self
        


class LoginIn(BaseModel):
    identifier: str # username or email
    password: str

class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    avatar_url: str | None

    model_config = {"from_attributes": True}

# SESSION HELPERS

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
    )

    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or invalid")

    return user

# ROUTES

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, response: Response, db: Session = Depends(get_db)):
    taken = db.scalar(select(User).where(func.lower(User.username) == body.username.lower()))

    if taken:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username is taken!")

    user = User(
        username=body.username, 
        password_hash=hash_password(body.password),
        email=body.email.strip().lower(),
        display_name=body.display_name.strip()
        )
    db.add(user)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Username is taken")

    start_session(db, user, response)
    user.last_login_at = func.now()
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=UserOut)
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    ident = body.identifier.strip().lower()
    column = User.email if "@" in ident else User.username
    user = db.scalar(select(User).where(func.lower(column) == ident))

    valid, new_hash = verify_password(body.password, user.password_hash if user else None)

    if not user or not valid or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password!")

    if new_hash:
        user.password_hash = new_hash

    start_session(db, user, response)
    user.last_login_at = func.now()
    db.commit()
    db.refresh(user)
    return user

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db)
):
    if session_token:
        db.execute(delete(UserSession).where(UserSession.token_hash == hash_token(session_token)))
        db.commit()
    response.delete_cookie(COOKIE_NAME)

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user