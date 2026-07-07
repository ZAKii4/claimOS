from typing import List
from fastapi import WebSocket


class ReviewConnectionManager:
    """
    Manages WebSocket connections for real-time inbox updates and locking presence.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_lock(self, claim_id: str, operator_id: str):
        message = {"event": "LOCKED", "claim_id": claim_id, "operator_id": operator_id}
        for connection in self.active_connections:
            await connection.send_json(message)

    async def broadcast_unlock(self, claim_id: str):
        message = {"event": "UNLOCKED", "claim_id": claim_id}
        for connection in self.active_connections:
            await connection.send_json(message)


review_manager = ReviewConnectionManager()
