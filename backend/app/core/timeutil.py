"""
Timezone helpers.

Recent SQLModel versions refuse to store timezone-naive datetimes, older ones accept either. Everything this app writes
or compares is therefore timezone-aware UTC. SQLite hands values back without a timezone, so `as_utc` re-attaches UTC
when reading and normalises anything a client sends.
"""
from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
