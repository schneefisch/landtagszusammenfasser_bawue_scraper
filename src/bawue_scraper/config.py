"""Application configuration loaded from environment variables."""

from typing import Literal

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
    ltzf_mode: Literal["dry-run", "live"] = "dry-run"
    openai_api_key: str | None = None
    scrape_interval_hours: int = 24
    scrape_lookback_days: int = 7
    parlis_request_delay_s: float = 1.0
    log_level: str = "INFO"
    cache_dir: str = "./cache"
    wahlperiode: int = 17
