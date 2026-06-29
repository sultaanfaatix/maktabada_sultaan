from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    data_dir: Path
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        token = os.getenv("BOT_TOKEN", "").strip()
        admin_id = os.getenv("ADMIN_ID", "").strip()
        if not token:
            raise RuntimeError("BOT_TOKEN is required. Copy .env.example to .env and set your Telegram bot token.")
        if not admin_id.isdigit():
            raise RuntimeError("ADMIN_ID is required and must be a Telegram numeric user ID.")

        return cls(
            bot_token=token,
            admin_id=int(admin_id),
            data_dir=Path(os.getenv("DATA_DIR", "/data")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
