from __future__ import annotations

from fastapi import APIRouter, Request

from app import db
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    db_ok = False
    try:
        db_ok = await db.ping_db()
    except Exception:
        db_ok = False

    mqtt_worker = getattr(request.app.state, "mqtt_worker", None)
    mqtt_ok = bool(mqtt_worker and mqtt_worker.connected)

    status = "ok" if db_ok and mqtt_ok else "degraded"
    return HealthResponse(
        status=status,
        database="up" if db_ok else "down",
        mqtt="up" if mqtt_ok else "down",
    )
