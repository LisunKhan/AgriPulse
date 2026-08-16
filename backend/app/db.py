from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

import asyncpg

from app.config import settings

_pool: Optional[asyncpg.Pool] = None

_TELEMETRY_COLUMNS = (
    "public_id, device_id, temperature_c, humidity_pct, lat, lng, status, recorded_at"
)
_ALERT_COLUMNS = (
    "public_id, device_id, alert_type, message, temperature_c, humidity_pct, "
    "created_at, acknowledged"
)


async def connect_db() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=10)
        await ensure_schema(_pool)
    return _pool


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _pool


async def ensure_schema(pool: asyncpg.Pool) -> None:
    """Apply hybrid public_id migration for existing databases."""
    migration = Path(__file__).resolve().parents[2] / "database" / "migrate_public_id.sql"
    # In the Docker image only backend/ is copied, so embed SQL fallback.
    if migration.exists():
        sql = migration.read_text(encoding="utf-8")
    else:
        sql = _EMBEDDED_PUBLIC_ID_MIGRATION
    async with pool.acquire() as conn:
        await conn.execute(sql)


_EMBEDDED_PUBLIC_ID_MIGRATION = """
ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS public_id UUID;
UPDATE telemetry SET public_id = gen_random_uuid() WHERE public_id IS NULL;
ALTER TABLE telemetry ALTER COLUMN public_id SET DEFAULT gen_random_uuid();
DO $$ BEGIN
    ALTER TABLE telemetry ALTER COLUMN public_id SET NOT NULL;
EXCEPTION WHEN others THEN NULL;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS idx_telemetry_public_id ON telemetry (public_id);

ALTER TABLE alerts ADD COLUMN IF NOT EXISTS public_id UUID;
UPDATE alerts SET public_id = gen_random_uuid() WHERE public_id IS NULL;
ALTER TABLE alerts ALTER COLUMN public_id SET DEFAULT gen_random_uuid();
DO $$ BEGIN
    ALTER TABLE alerts ALTER COLUMN public_id SET NOT NULL;
EXCEPTION WHEN others THEN NULL;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_public_id ON alerts (public_id);
"""


def _row_to_dict(row: asyncpg.Record) -> dict[str, Any]:
    data = dict(row)
    if "public_id" in data and data["public_id"] is not None:
        data["public_id"] = str(data["public_id"])
    data.pop("id", None)
    return data


async def insert_telemetry(
    *,
    device_id: str,
    temperature_c: float,
    humidity_pct: float,
    lat: float,
    lng: float,
    status: str,
    recorded_at: datetime,
) -> dict[str, Any]:
    pool = get_pool()
    row = await pool.fetchrow(
        f"""
        INSERT INTO telemetry (
            device_id, temperature_c, humidity_pct, lat, lng, status, recorded_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING {_TELEMETRY_COLUMNS}
        """,
        device_id,
        temperature_c,
        humidity_pct,
        lat,
        lng,
        status,
        recorded_at,
    )
    return _row_to_dict(row)


async def insert_alert(
    *,
    device_id: str,
    alert_type: str,
    message: str,
    temperature_c: float,
    humidity_pct: float,
) -> dict[str, Any]:
    pool = get_pool()
    row = await pool.fetchrow(
        f"""
        INSERT INTO alerts (
            device_id, alert_type, message, temperature_c, humidity_pct
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING {_ALERT_COLUMNS}
        """,
        device_id,
        alert_type,
        message,
        temperature_c,
        humidity_pct,
    )
    return _row_to_dict(row)


async def fetch_latest_telemetry() -> list[dict[str, Any]]:
    pool = get_pool()
    rows = await pool.fetch(
        f"""
        SELECT DISTINCT ON (device_id)
            {_TELEMETRY_COLUMNS}
        FROM telemetry
        ORDER BY device_id, recorded_at DESC
        """
    )
    return [_row_to_dict(r) for r in rows]


async def fetch_telemetry_history(
    *,
    device_id: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    pool = get_pool()
    limit = max(1, min(limit, 500))
    if device_id:
        rows = await pool.fetch(
            f"""
            SELECT {_TELEMETRY_COLUMNS}
            FROM telemetry
            WHERE device_id = $1
            ORDER BY recorded_at DESC
            LIMIT $2
            """,
            device_id,
            limit,
        )
    else:
        rows = await pool.fetch(
            f"""
            SELECT {_TELEMETRY_COLUMNS}
            FROM telemetry
            ORDER BY recorded_at DESC
            LIMIT $1
            """,
            limit,
        )
    return [_row_to_dict(r) for r in rows]


async def fetch_alerts(
    *,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    pool = get_pool()
    limit = max(1, min(limit, 500))
    if acknowledged is None:
        rows = await pool.fetch(
            f"""
            SELECT {_ALERT_COLUMNS}
            FROM alerts
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
    else:
        rows = await pool.fetch(
            f"""
            SELECT {_ALERT_COLUMNS}
            FROM alerts
            WHERE acknowledged = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            acknowledged,
            limit,
        )
    return [_row_to_dict(r) for r in rows]


async def acknowledge_alert(public_id: UUID) -> Optional[dict[str, Any]]:
    pool = get_pool()
    row = await pool.fetchrow(
        f"""
        UPDATE alerts
        SET acknowledged = TRUE
        WHERE public_id = $1
        RETURNING {_ALERT_COLUMNS}
        """,
        public_id,
    )
    return _row_to_dict(row) if row else None


async def ping_db() -> bool:
    pool = get_pool()
    value = await pool.fetchval("SELECT 1")
    return value == 1
