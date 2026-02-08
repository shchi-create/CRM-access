import os
from dataclasses import dataclass
from typing import List


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    env: str
    google_service_account_json: str
    spreadsheet_id: str
    api_key: str
    x_api_key_header_name: str
    allowed_user_ids: List[str]
    telegram_bot_token: str
    cache_ttl: int
    rate_limit_per_min: int
    max_search_results: int
    log_level: str
    sentry_dsn: str
    max_sheet_rows: int


    @classmethod
    def from_env(cls) -> "Settings":
        env = os.getenv("ENV", "dev")
        log_level = os.getenv("LOG_LEVEL", "INFO" if env == "production" else "DEBUG")
        return cls(
            env=env,
            google_service_account_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", ""),
            spreadsheet_id=os.getenv("SPREADSHEET_ID", ""),
            api_key=os.getenv("API_KEY", ""),
            x_api_key_header_name=os.getenv("X_API_KEY_HEADER_NAME", "x-api-key"),
            allowed_user_ids=_split_csv(os.getenv("ALLOWED_USER_IDS", "")),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            cache_ttl=int(os.getenv("CACHE_TTL", "300")),
            rate_limit_per_min=int(os.getenv("RATE_LIMIT_PER_MIN", "60")),
            max_search_results=int(os.getenv("MAX_SEARCH_RESULTS", "20")),
            log_level=log_level,
            sentry_dsn=os.getenv("SENTRY_DSN", ""),
            max_sheet_rows=int(os.getenv("MAX_SHEET_ROWS", "50000")),
        )


settings = Settings.from_env()
