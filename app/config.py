from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "VitalSync"
    environment: str = "development"

    # Defaults to SQLite so the app runs with zero external services for
    # local hacking. docker-compose overrides this to Postgres.
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    outbox_exchange: str = "vitalsync.events"

    redis_url: str = "redis://localhost:6379/0"

    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60


settings = Settings()
