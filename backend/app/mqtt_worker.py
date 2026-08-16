from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime, timezone
from typing import Any, Optional

import paho.mqtt.client as mqtt

from app import db
from app.config import settings
from app.thresholds import evaluate_thresholds
from app.ws_hub import hub

logger = logging.getLogger("agripulse.mqtt")


class MqttIngestor:
    """Background MQTT subscriber that persists telemetry and raises alerts."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._last_alert_at: dict[tuple[str, str], float] = {}

    @property
    def connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        try:
            client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=f"agripulse-backend-{random.randint(1000, 9999)}",
            )
        except AttributeError:
            client = mqtt.Client(client_id=f"agripulse-backend-{random.randint(1000, 9999)}")

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        self._client = client

        client.connect_async(settings.mqtt_host, settings.mqtt_port, keepalive=60)
        client.loop_start()
        logger.info("MQTT client starting toward %s:%s", settings.mqtt_host, settings.mqtt_port)

    def stop(self) -> None:
        if self._client is None:
            return
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False
        logger.info("MQTT client stopped")

    def _on_connect(self, client: mqtt.Client, _userdata: Any, _flags: Any, reason_code: int, _properties: Any = None) -> None:
        # paho v1 passes rc as int; v2 uses reason_code similarly for success=0
        rc = int(getattr(reason_code, "value", reason_code))
        if rc == 0:
            self._connected = True
            client.subscribe(settings.mqtt_topic, qos=1)
            logger.info("MQTT connected; subscribed to %s", settings.mqtt_topic)
        else:
            self._connected = False
            logger.error("MQTT connect failed rc=%s", rc)

    def _on_disconnect(self, _client: mqtt.Client, _userdata: Any, _flags: Any, reason_code: int = 0, _properties: Any = None) -> None:
        self._connected = False
        logger.warning("MQTT disconnected rc=%s", reason_code)

    def _on_message(self, _client: mqtt.Client, _userdata: Any, message: mqtt.MQTTMessage) -> None:
        asyncio.run_coroutine_threadsafe(self._handle_message(message), self._loop)

    async def _handle_message(self, message: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning("Invalid MQTT payload on %s: %s", message.topic, exc)
            return

        try:
            device_id = str(payload["device_id"])
            temperature_c = float(payload["temperature_c"])
            humidity_pct = float(payload["humidity_pct"])
            lat = float(payload["lat"])
            lng = float(payload["lng"])
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Malformed telemetry fields: %s | payload=%s", exc, payload)
            return

        recorded_at = self._parse_timestamp(payload.get("recorded_at"))
        evaluation = evaluate_thresholds(temperature_c, humidity_pct)
        # Prefer backend evaluation as source of truth for status
        status = evaluation.status

        try:
            record = await db.insert_telemetry(
                device_id=device_id,
                temperature_c=temperature_c,
                humidity_pct=humidity_pct,
                lat=lat,
                lng=lng,
                status=status,
                recorded_at=recorded_at,
            )
        except Exception:
            logger.exception("Failed to insert telemetry for %s", device_id)
            return

        await hub.broadcast("telemetry", record)

        if evaluation.alert_type and evaluation.message:
            if self._should_raise_alert(device_id, evaluation.alert_type):
                try:
                    alert = await db.insert_alert(
                        device_id=device_id,
                        alert_type=evaluation.alert_type,
                        message=evaluation.message,
                        temperature_c=temperature_c,
                        humidity_pct=humidity_pct,
                    )
                    await hub.broadcast("alert", alert)
                    logger.info("Alert raised for %s: %s", device_id, evaluation.alert_type)
                except Exception:
                    logger.exception("Failed to insert alert for %s", device_id)

    def _should_raise_alert(self, device_id: str, alert_type: str) -> bool:
        key = (device_id, alert_type)
        now = asyncio.get_event_loop().time()
        last = self._last_alert_at.get(key)
        if last is not None and (now - last) < settings.alert_cooldown_sec:
            return False
        self._last_alert_at[key] = now
        return True

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, str) and value:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.now(timezone.utc)
