from typing import List, Dict, Any
from pydantic import BaseModel, Field
import uuid
import time


class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author: str
    content: str
    room_id: str
    timestamp: float = Field(default_factory=time.time)
    reactions: Dict[str, int] = {}
    mentions: List[str] = []
    is_resolved: bool = False
    replies: List['Comment'] = []


class ThreadManager:
    """Manages collaborative comments and threads."""

    _comments: Dict[str, Comment] = {}

    @classmethod
    def add_comment(cls, author: str, room_id: str, content: str, mentions: List[str] = None) -> Comment:
        c = Comment(
            author=author,
            room_id=room_id,
            content=content,
            mentions=mentions or []
        )
        cls._comments[c.id] = c
        return c

    @classmethod
    def resolve_comment(cls, comment_id: str) -> bool:
        if comment_id in cls._comments:
            cls._comments[comment_id].is_resolved = True
            return True
        return False

    @classmethod
    def add_reaction(cls, comment_id: str, emoji: str) -> bool:
        if comment_id in cls._comments:
            c = cls._comments[comment_id]
            c.reactions[emoji] = c.reactions.get(emoji, 0) + 1
            return True
        return False

    @classmethod
    def get_room_comments(cls, room_id: str) -> List[Comment]:
        return [c for c in cls._comments.values() if c.room_id == room_id]

    @classmethod
    def _reset(cls):
        cls._comments.clear()
