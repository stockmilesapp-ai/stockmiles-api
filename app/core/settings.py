from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    google_client_id: str
    session_cookie_name: str = "sm_session"
    session_days: int = 30
    cookie_secure: bool = True
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "https://stockmiles-web.vercel.app",
    ]


settings = Settings()
