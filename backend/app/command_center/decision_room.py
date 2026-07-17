from typing import Dict, Any, List
import uuid

class DecisionRoomEngine:
    """Virtual rooms where human experts and AI agents collaborate on critical cases."""

    _rooms: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create_room(cls, name: str, topic: str) -> Dict[str, Any]:
        r_id = str(uuid.uuid4())
        room = {
            "id": r_id,
            "name": name,
            "topic": topic,
            "participants": ["Fraud Agent", "Legal Agent"],
            "messages": [],
            "status": "OPEN"
        }
        cls._rooms[r_id] = room
        return room

    @classmethod
    def get_all_rooms(cls) -> List[Dict[str, Any]]:
        return list(cls._rooms.values())
