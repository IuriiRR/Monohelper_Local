import hmac

from fastapi import Header, HTTPException

from config import load_settings


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = load_settings()
    if not settings.internal_api_key:
        raise HTTPException(status_code=503, detail="INTERNAL_API_KEY is not configured")
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.internal_api_key):
        raise HTTPException(status_code=401, detail="invalid or missing API key")
