from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app import db
from app.schemas import AlertRecord

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRecord])
async def list_alerts(
    acknowledged: Optional[bool] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[AlertRecord]:
    rows = await db.fetch_alerts(acknowledged=acknowledged, limit=limit)
    return [AlertRecord(**row) for row in rows]


@router.post("/{alert_id}/ack", response_model=AlertRecord)
async def ack_alert(alert_id: int) -> AlertRecord:
    row = await db.acknowledge_alert(alert_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertRecord(**row)
