"""Application configuration using pydantic-settings."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Authentication
    api_key: str

    # Database
    database_url: str = "sqlite:///./ding.db"

    # SendGrid
    sendgrid_api_key: str
    sendgrid_from_email: str

    # Printer
    printer_vendor_id: str = "0x0416"
    printer_product_id: str = "0x5011"
    printer_device_path: str = "/dev/usb/lp0"

    # Application
    app_name: str = "DING"
    app_url: str = "http://localhost:8501"

    # Paths
    store_path: Path = Path("store")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure store directory exists
        self.store_path.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()
