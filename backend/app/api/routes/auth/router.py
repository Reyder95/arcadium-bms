from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User, UserSession
from app.api.dependencies import COOKIE_NAME, get_current_user, set_session_cookie
from app.job.enqueue import enqueue_tachi_seed
from app.schemas.job import JobOut
from app.core.security import hash_password, hash_token, verify_password

from app.schemas.auth import UserOut, RegisterIn, LoginIn

router = APIRouter(prefix="/auth", tags=["auth"])

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

    set_session_cookie(db, user, response)
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

    set_session_cookie(db, user, response)
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

# Allows a user to link their tachi account. Once this is done, a job is queued to seed them behind the scenes.

@router.put("/me/tachi_key", response_model=JobOut, status_code=200)
def tachi_key(tachi_key: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if (tachi_key == None or tachi_key == ""):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Tachi key must not be empty!")

    user.tachi_api_key = tachi_key.strip()
    user.rating_seeds = {}

    job = enqueue_tachi_seed(db, user.id)    

    db.commit()

    return job