from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app import db
from app.schemas import TelemetryRecord

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/latest", response_model=list[TelemetryRecord])
async def latest_telemetry() -> list[TelemetryRecord]:
    rows = await db.fetch_latest_telemetry()
    return [TelemetryRecord(**row) for row in rows]


@router.get("", response_model=list[TelemetryRecord])
async def telemetry_history(
    device_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[TelemetryRecord]:
    rows = await db.fetch_telemetry_history(device_id=device_id, limit=limit)
    return [TelemetryRecord(**row) for row in rows]
