from __future__ import annotations

from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class ThresholdResult:
    status: str
    alert_type: str | None
    message: str | None


def evaluate_thresholds(temperature_c: float, humidity_pct: float) -> ThresholdResult:
    """Canonical cold-chain rules used when ingesting MQTT payloads."""
    if temperature_c < settings.temp_min_c or temperature_c > settings.temp_max_c:
        return ThresholdResult(
            status="spoilage_risk",
            alert_type="temperature_breach",
            message=(
                f"Temperature {temperature_c}°C outside safe band "
                f"{settings.temp_min_c}–{settings.temp_max_c}°C"
            ),
        )

    if humidity_pct < settings.humidity_min_pct or humidity_pct > settings.humidity_max_pct:
        return ThresholdResult(
            status="warning",
            alert_type="humidity_breach",
            message=(
                f"Humidity {humidity_pct}% outside safe band "
                f"{settings.humidity_min_pct}–{settings.humidity_max_pct}%"
            ),
        )

    return ThresholdResult(status="ok", alert_type=None, message=None)
