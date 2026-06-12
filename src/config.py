import os

from pydantic import BaseModel


class Settings(BaseModel):
    internal_api_key: str = ""
    admin_password: str = ""
    report_timezone: str = "Europe/Kyiv"


def load_settings() -> Settings:
    return Settings(
        internal_api_key=(os.getenv("INTERNAL_API_KEY") or "").strip(),
        admin_password=(os.getenv("ADMIN_PASSWORD") or "").strip(),
        report_timezone=(os.getenv("REPORT_TIMEZONE") or "Europe/Kyiv").strip(),
    )
