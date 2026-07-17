import time
from typing import Dict, Any, List

class PresenceManager:
    """Manages the real-time presence of users across different rooms."""

    # Format: { room_id: { user_id: { status, location, last_heartbeat } } }
    _rooms: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def join_room(cls, room_id: str, user_id: str) -> bool:
        if room_id not in cls._rooms:
            cls._rooms[room_id] = {}
        
        cls._rooms[room_id][user_id] = {
            "status": "online",
            "location": "dashboard",
            "last_heartbeat": time.time()
        }
        return True

    @classmethod
    def leave_room(cls, room_id: str, user_id: str) -> bool:
        if room_id in cls._rooms and user_id in cls._rooms[room_id]:
            del cls._rooms[room_id][user_id]
            return True
        return False

    @classmethod
    def update_presence(cls, room_id: str, user_id: str, status: str, location: str) -> bool:
        if room_id in cls._rooms and user_id in cls._rooms[room_id]:
            cls._rooms[room_id][user_id].update({
                "status": status,
                "location": location,
                "last_heartbeat": time.time()
            })
            return True
        return False

    @classmethod
    def get_room_presence(cls, room_id: str) -> Dict[str, Any]:
        """Returns presence data, marking inactive users as offline."""
        now = time.time()
        if room_id not in cls._rooms:
            return {}
            
        presence = {}
        for uid, data in cls._rooms[room_id].items():
            # If heartbeat older than 30s, mark offline
            if now - data["last_heartbeat"] > 30:
                data["status"] = "offline"
            presence[uid] = data
            
        return presence

    @classmethod
    def _reset(cls):
        cls._rooms.clear()
