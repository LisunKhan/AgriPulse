"""
AgriPulse IoT sensor simulator (Milestone 1).

Publishes mock cold-chain telemetry to Mosquitto every few seconds,
simulating trucks moving perishable goods toward Melbourne.
"""

from __future__ import annotations

import json
import os
import random
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Any

import paho.mqtt.client as mqtt

# --- Config (override with env vars) ---
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
PUBLISH_INTERVAL_SEC = float(os.getenv("PUBLISH_INTERVAL_SEC", "5"))
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "agripulse/telemetry")

# Safe cold-chain band (vaccines / chilled produce)
TEMP_MIN_C = float(os.getenv("TEMP_MIN_C", "2.0"))
TEMP_MAX_C = float(os.getenv("TEMP_MAX_C", "8.0"))
SPIKE_CHANCE = float(os.getenv("SPIKE_CHANCE", "0.12"))  # occasional breach

# Rough Victorian inland → Melbourne path seeds
TRUCKS = [
    {
        "device_id": "truck_01",
        "cargo": "vaccines",
        "lat": -36.7589,
        "lng": 144.2784,  # Bendigo area
    },
    {
        "device_id": "truck_02",
        "cargo": "fresh_produce",
        "lat": -36.3833,
        "lng": 145.4000,  # Shepparton area
    },
    {
        "device_id": "truck_03",
        "cargo": "dairy",
        "lat": -38.1460,
        "lng": 144.3480,  # Geelong approach
    },
]

MELBOURNE = {"lat": -37.8136, "lng": 144.9631}

_running = True


def _handle_signal(_signum: int, _frame: Any) -> None:
    global _running
    _running = False


def classify_status(temperature_c: float, humidity_pct: float) -> str:
    """Simple threshold logic the backend will later formalize."""
    if temperature_c < TEMP_MIN_C or temperature_c > TEMP_MAX_C:
        return "spoilage_risk"
    if humidity_pct > 90 or humidity_pct < 40:
        return "warning"
    return "ok"


def drift_toward_melbourne(lat: float, lng: float) -> tuple[float, float]:
    """Nudge GPS a little closer to Melbourne each tick."""
    step = random.uniform(0.01, 0.04)
    new_lat = lat + (MELBOURNE["lat"] - lat) * step
    new_lng = lng + (MELBOURNE["lng"] - lng) * step
    # Small road noise
    new_lat += random.uniform(-0.002, 0.002)
    new_lng += random.uniform(-0.002, 0.002)
    return round(new_lat, 6), round(new_lng, 6)


def build_reading(truck: dict[str, Any]) -> dict[str, Any]:
    temperature_c = round(random.uniform(TEMP_MIN_C + 0.3, TEMP_MAX_C - 0.3), 2)
    if random.random() < SPIKE_CHANCE:
        # Simulate door open / refrigeration fault
        temperature_c = round(random.uniform(TEMP_MAX_C + 1.5, TEMP_MAX_C + 6.0), 2)

    humidity_pct = round(random.uniform(55.0, 88.0), 2)
    lat, lng = drift_toward_melbourne(truck["lat"], truck["lng"])
    truck["lat"], truck["lng"] = lat, lng

    status = classify_status(temperature_c, humidity_pct)

    return {
        "device_id": truck["device_id"],
        "cargo": truck["cargo"],
        "temperature_c": temperature_c,
        "humidity_pct": humidity_pct,
        "lat": lat,
        "lng": lng,
        "status": status,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def on_connect(client: mqtt.Client, _userdata: Any, _flags: Any, reason_code: int, _properties: Any = None) -> None:
    if reason_code == 0:
        print(f"[mqtt] connected to {MQTT_HOST}:{MQTT_PORT}")
    else:
        print(f"[mqtt] connect failed reason_code={reason_code}", file=sys.stderr)


def create_client() -> mqtt.Client:
    # paho-mqtt v2 callback API; falls back cleanly on v1 if needed
    try:
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"agripulse-simulator-{random.randint(1000, 9999)}",
        )
    except AttributeError:
        client = mqtt.Client(client_id=f"agripulse-simulator-{random.randint(1000, 9999)}")

    client.on_connect = on_connect
    return client


def main() -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    client = create_client()

    print(
        f"[sim] AgriPulse sensor simulator starting "
        f"(interval={PUBLISH_INTERVAL_SEC}s, trucks={len(TRUCKS)})"
    )

    while _running:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            break
        except OSError as exc:
            print(f"[mqtt] broker unavailable ({exc}); retrying in 3s...")
            time.sleep(3)

    client.loop_start()

    try:
        while _running:
            for truck in TRUCKS:
                payload = build_reading(truck)
                topic = f"{TOPIC_PREFIX}/{payload['device_id']}"
                body = json.dumps(payload)
                result = client.publish(topic, body, qos=1)
                result.wait_for_publish(timeout=5)

                flag = "!" if payload["status"] != "ok" else " "
                print(
                    f"{flag} [{payload['device_id']}] "
                    f"temp={payload['temperature_c']}°C "
                    f"hum={payload['humidity_pct']}% "
                    f"status={payload['status']} "
                    f"@ ({payload['lat']}, {payload['lng']})"
                )

            time.sleep(PUBLISH_INTERVAL_SEC)
    finally:
        client.loop_stop()
        client.disconnect()
        print("[sim] stopped")


if __name__ == "__main__":
    main()
