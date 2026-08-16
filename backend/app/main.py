from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app import db
from app.config import settings
from app.mqtt_worker import MqttIngestor
from app.routes import alerts, health, telemetry
from app.ws_hub import hub

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("agripulse.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect_db()
    logger.info("Connected to PostgreSQL")

    loop = asyncio.get_running_loop()
    mqtt_worker = MqttIngestor(loop)
    mqtt_worker.start()
    app.state.mqtt_worker = mqtt_worker

    try:
        yield
    finally:
        mqtt_worker.stop()
        await db.close_db()
        logger.info("Shutdown complete")


app = FastAPI(title=settings.app_name, version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(telemetry.router)
app.include_router(alerts.router)


@app.websocket("/ws/telemetry")
async def telemetry_ws(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    try:
        while True:
            # Keep connection alive; clients may send pings/acks
            await websocket.receive_text()
    except WebSocketDisconnect:
        await hub.disconnect(websocket)
    except Exception:
        await hub.disconnect(websocket)
