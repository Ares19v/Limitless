"""FastAPI dependencies (injected via Depends)."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from fastapi import Depends


def get_app_settings(settings: Settings = Depends(get_settings)) -> Settings:
    return settings
