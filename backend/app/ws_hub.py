from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket


class TelemetryHub:
    """Fan-out live telemetry/alert events to connected WebSocket clients."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)

    async def broadcast(self, event: str, payload: dict[str, Any]) -> None:
        message = json.dumps({"event": event, "data": payload})
        async with self._lock:
            clients = list(self._clients)

        stale: list[WebSocket] = []
        for client in clients:
            try:
                await client.send_text(message)
            except Exception:
                stale.append(client)

        if stale:
            async with self._lock:
                for client in stale:
                    self._clients.discard(client)


hub = TelemetryHub()
