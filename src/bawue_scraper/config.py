"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """BaWue Scraper configuration.

    All values can be set via environment variables or a .env file.
    """

    model_config = {"env_prefix": "", "env_file": ".env", "env_file_encoding": "utf-8"}

    # Required
    ltzf_api_url: str = "http://localhost:8080"
    ltzf_api_key: str = ""
    collector_id: str = "bawue-scraper"

    # Optional
    ltzf_mode: str = "dry-run"  # "dry-run" (default, logs only) or "live" (HTTP calls)
    openai_api_key: str | None = None
    scrape_interval_hours: int = 24
    parlis_request_delay_s: float = 1.0
    log_level: str = "INFO"
    cache_dir: str = "./cache"
    wahlperiode: int = 17
