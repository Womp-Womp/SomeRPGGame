from typing import Optional

from ..config import DB_URL


def get_engine() -> Optional[object]:
    try:
        from sqlalchemy import create_engine  # type: ignore

        return create_engine(DB_URL)
    except Exception:
        # SQLAlchemy not installed or misconfigured; return None to indicate unavailable
        return None

