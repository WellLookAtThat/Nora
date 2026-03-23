from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    token: str
    command_prefix: str
    status_rotation_seconds: int
    log_level: str


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DISCORD_TOKEN is missing. Add it to your .env file.")

    prefix = os.getenv("COMMAND_PREFIX", "!").strip() or "!"
    rotation_seconds = int(os.getenv("STATUS_ROTATION_SECONDS", "45"))
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    return Settings(
        token=token,
        command_prefix=prefix,
        status_rotation_seconds=rotation_seconds,
        log_level=log_level,
    )
