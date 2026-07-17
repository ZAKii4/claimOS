from typing import Dict, Any


class TransportManager:
    """Handles multiple MCP communication transports (STDIO, HTTP, WS, SSE)."""

    _transports = ["STDIO", "HTTP", "WebSocket", "SSE"]

    @classmethod
    def get_available_transports(cls) -> list[str]:
        return cls._transports

    @classmethod
    def connect(cls, server_id: str, transport_type: str) -> Dict[str, Any]:
        """Simulates establishing a connection using a specific transport."""
        if transport_type not in cls._transports:
            return {"status": "ERROR", "message": f"Unsupported transport {transport_type}"}
            
        return {
            "status": "CONNECTED",
            "server_id": server_id,
            "transport": transport_type,
            "latency_ms": 15.0 if transport_type == "STDIO" else 45.0
        }

    @classmethod
    def disconnect(cls, server_id: str) -> bool:
        """Simulates closing the transport connection."""
        return True
