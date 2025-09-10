import os
from typing import Optional

try:
    # Load .env if present (no-op otherwise)
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass


def _get_str(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(name, default)


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


# Environment variables
DISCORD_BOT_TOKEN: Optional[str] = _get_str("DISCORD_BOT_TOKEN")
GEMINI_API_KEY: Optional[str] = _get_str("GEMINI_API_KEY")
DB_URL: str = _get_str("ASTRARPG_DB_URL", "sqlite:///astrarpg.db") or "sqlite:///astrarpg.db"
ENV: str = _get_str("ASTRARPG_ENV", "dev") or "dev"
DEFAULT_TEMPERATURE: float = _get_float("ASTRARPG_DEFAULT_TEMPERATURE", 0.9)
THINKING_BUDGET: int = _get_int("ASTRARPG_THINKING_BUDGET", -1)

__all__ = [
    "DISCORD_BOT_TOKEN",
    "GEMINI_API_KEY",
    "DB_URL",
    "ENV",
    "DEFAULT_TEMPERATURE",
    "THINKING_BUDGET",
]

