from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from pydantic import BaseModel

from app.collaboration.presence import PresenceManager
from app.collaboration.websockets import manager
from app.collaboration.activity import ActivityManager
from app.collaboration.comments import ThreadManager
from app.collaboration.conflicts import ConflictResolutionEngine
from app.collaboration.whiteboard import WhiteboardManager
from app.collaboration.calendar import CalendarManager
from app.collaboration.analytics import TeamAnalyticsEngine

router = APIRouter(prefix="/collaboration", tags=["Real-Time Collaboration"])


class CommentRequest(BaseModel):
    author: str
    room_id: str
    content: str
    mentions: List[str] = []


class MentionRequest(BaseModel):
    comment_id: str
    emoji: str


class MergeRequest(BaseModel):
    doc_id: str
    data: Any
    client_version: int


class WhiteboardRequest(BaseModel):
    board_id: str
    elements: List[Dict[str, Any]]


@router.websocket("/ws/{room_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, client_id: str):
    await manager.connect(websocket, room_id)
    PresenceManager.join_room(room_id, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # In a real scenario, process different event types (cursor move, etc.)
            await manager.broadcast(f"Client {client_id} says: {data}", room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        PresenceManager.leave_room(room_id, client_id)
        await manager.broadcast(f"Client {client_id} left the room", room_id)


@router.get("/presence/{room_id}")
def get_presence(room_id: str):
    return PresenceManager.get_room_presence(room_id)


@router.get("/activity/{room_id}")
def get_activity(room_id: str):
    return ActivityManager.get_feed(room_id)


@router.get("/comments/{room_id}")
def get_comments(room_id: str):
    return ThreadManager.get_room_comments(room_id)


@router.post("/comments")
def post_comment(req: CommentRequest):
    comment = ThreadManager.add_comment(req.author, req.room_id, req.content, req.mentions)
    ActivityManager.emit_event(req.author, req.room_id, "comment", req.content)
    return comment


@router.post("/mentions")
def post_reaction(req: MentionRequest):
    return ThreadManager.add_reaction(req.comment_id, req.emoji)


@router.post("/merge")
def post_merge(req: MergeRequest):
    status, doc = ConflictResolutionEngine.process_edit(req.doc_id, req.data, req.client_version)
    return {"status": status, "document": doc}


@router.post("/whiteboard")
def update_whiteboard(req: WhiteboardRequest):
    return WhiteboardManager.update_board(req.board_id, req.elements)


@router.get("/calendar")
def get_calendar():
    return CalendarManager.get_events()


@router.get("/analytics/{room_id}")
def get_analytics(room_id: str):
    feed = ActivityManager.get_feed(room_id)
    return TeamAnalyticsEngine.compute_team_metrics(feed)
