from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TelemetryReading(BaseModel):
    device_id: str
    temperature_c: float
    humidity_pct: float
    lat: float
    lng: float
    status: str
    recorded_at: datetime
    cargo: Optional[str] = None


class TelemetryRecord(TelemetryReading):
    id: int


class AlertRecord(BaseModel):
    id: int
    device_id: str
    alert_type: str
    message: str
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    created_at: datetime
    acknowledged: bool


class HealthResponse(BaseModel):
    status: str
    database: str
    mqtt: str
    app: str = Field(default="AgriPulse API")
