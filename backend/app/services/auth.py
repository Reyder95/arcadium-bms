from sqlalchemy.orm import Session
from app.models import User, UserSession
from app.core.security import new_session_token, hash_token
from datetime import datetime, timezone, timedelta
from app.config import settings

def create_session(db: Session, user: User) -> str:
    token = new_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.session_days)
    db.add(UserSession(user_id=user.id, token_hash=hash_token(token), expires_at=expires_at))
    return token