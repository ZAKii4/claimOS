from typing import Dict, List, Any


class WhiteboardManager:
    """Manages state for live shared whiteboards."""

    # { board_id: { elements: List[Dict], version: int } }
    _boards: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_board(cls, board_id: str) -> Dict[str, Any]:
        if board_id not in cls._boards:
            cls._boards[board_id] = {"elements": [], "version": 0}
        return cls._boards[board_id]

    @classmethod
    def update_board(cls, board_id: str, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        board = cls.get_board(board_id)
        board["elements"] = elements
        board["version"] += 1
        return board

    @classmethod
    def _reset(cls):
        cls._boards.clear()
