import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter(prefix="/logs", tags=["Live Logs"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

log_manager = ConnectionManager()

# Background task to simulate live logs for the dashboard since we don't have
# a true event bus wired up across the entire system yet.
async def log_generator():
    import random
    events = [
        {"level": "INFO", "source": "DocumentPipeline", "message": "Received new claim file."},
        {"level": "INFO", "source": "OCREngine", "message": "Extracted text from invoice."},
        {"level": "INFO", "source": "ValidationEngine", "message": "Checking cross-reference with policy..."},
        {"level": "WARN", "source": "FraudEngine", "message": "Unusual pattern detected in metadata."},
        {"level": "INFO", "source": "DecisionEngine", "message": "Claim classified as STP_APPROVED."}
    ]
    while True:
        await asyncio.sleep(random.uniform(2.0, 5.0))
        event = random.choice(events)
        await log_manager.broadcast(json.dumps(event))


@router.websocket("/ws")
async def websocket_logs(websocket: WebSocket):
    await log_manager.connect(websocket)
    try:
        while True:
            # Keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        log_manager.disconnect(websocket)
