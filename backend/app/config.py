from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    cookie_secure: bool = False
    session_days: int = 30

settings = Settings()