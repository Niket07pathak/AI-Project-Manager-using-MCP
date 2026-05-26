import os


DEFAULT_DEV_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def app_env() -> str:
    return os.getenv("APP_ENV", "development").strip().lower()


def is_development() -> bool:
    return app_env() == "development"


def bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def allowed_origins() -> list[str]:
    configured = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ALLOWED_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    if is_development():
        return list(DEFAULT_DEV_ORIGINS)
    return []


def api_docs_enabled() -> bool:
    return bool_env("ENABLE_API_DOCS", default=is_development())


def expose_error_details() -> bool:
    return bool_env("ENABLE_ERROR_DETAILS", default=is_development())
