"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Swaarm application settings."""

    # App
    app_name: str = "Swaarm API"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # OpenAI
    openai_api_key: str = ""
    swaarm_llm_model: str = "gpt-4o-mini"  # Renamed to avoid collision with Claude Code env var

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Sentry
    sentry_dsn: str = ""

    # Serper (web enrichment)
    serper_api_key: str = ""

    # Simulation defaults
    default_agent_count: int = 200
    default_round_count: int = 50
    max_concurrent_llm_calls: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
