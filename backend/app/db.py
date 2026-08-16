from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import asyncpg

from app.config import settings

_pool: Optional[asyncpg.Pool] = None


async def connect_db() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=10)
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
        """
        INSERT INTO telemetry (
            device_id, temperature_c, humidity_pct, lat, lng, status, recorded_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id, device_id, temperature_c, humidity_pct, lat, lng, status, recorded_at
        """,
        device_id,
        temperature_c,
        humidity_pct,
        lat,
        lng,
        status,
        recorded_at,
    )
    return dict(row)


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
        """
        INSERT INTO alerts (
            device_id, alert_type, message, temperature_c, humidity_pct
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, device_id, alert_type, message, temperature_c, humidity_pct,
                  created_at, acknowledged
        """,
        device_id,
        alert_type,
        message,
        temperature_c,
        humidity_pct,
    )
    return dict(row)


async def fetch_latest_telemetry() -> list[dict[str, Any]]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT DISTINCT ON (device_id)
            id, device_id, temperature_c, humidity_pct, lat, lng, status, recorded_at
        FROM telemetry
        ORDER BY device_id, recorded_at DESC
        """
    )
    return [dict(r) for r in rows]


async def fetch_telemetry_history(
    *,
    device_id: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    pool = get_pool()
    limit = max(1, min(limit, 500))
    if device_id:
        rows = await pool.fetch(
            """
            SELECT id, device_id, temperature_c, humidity_pct, lat, lng, status, recorded_at
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
            """
            SELECT id, device_id, temperature_c, humidity_pct, lat, lng, status, recorded_at
            FROM telemetry
            ORDER BY recorded_at DESC
            LIMIT $1
            """,
            limit,
        )
    return [dict(r) for r in rows]


async def fetch_alerts(
    *,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    pool = get_pool()
    limit = max(1, min(limit, 500))
    if acknowledged is None:
        rows = await pool.fetch(
            """
            SELECT id, device_id, alert_type, message, temperature_c, humidity_pct,
                   created_at, acknowledged
            FROM alerts
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
    else:
        rows = await pool.fetch(
            """
            SELECT id, device_id, alert_type, message, temperature_c, humidity_pct,
                   created_at, acknowledged
            FROM alerts
            WHERE acknowledged = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            acknowledged,
            limit,
        )
    return [dict(r) for r in rows]


async def acknowledge_alert(alert_id: int) -> Optional[dict[str, Any]]:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        UPDATE alerts
        SET acknowledged = TRUE
        WHERE id = $1
        RETURNING id, device_id, alert_type, message, temperature_c, humidity_pct,
                  created_at, acknowledged
        """,
        alert_id,
    )
    return dict(row) if row else None


async def ping_db() -> bool:
    pool = get_pool()
    value = await pool.fetchval("SELECT 1")
    return value == 1
