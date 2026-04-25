from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class Settings:
    project_name: str = os.getenv("PROJECT_NAME", "Campus Academic Activity Recommender")
    env: str = os.getenv("ENV", "development")
    api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api/v1")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://se_user:se_password@localhost:3306/se_project",
    )
    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])


settings = Settings()
