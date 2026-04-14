from __future__ import annotations

from datetime import UTC, datetime
from .db import get_conn

def set_profile(key: str, value: str) -> None:
    now = datetime.now(UTC).isoformat()
    with get_conn() as conn:
        conn.execute(
            '''
            INSERT INTO profile (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            ''',
            (key, value, now),
        )
        conn.commit()

def get_profile() -> dict[str, str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT key, value FROM profile ORDER BY key").fetchall()
    return {row["key"]: row["value"] for row in rows}
