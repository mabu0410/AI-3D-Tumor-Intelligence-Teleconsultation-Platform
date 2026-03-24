"""
Module 6 — WebSocket Manager
Real-time multi-user annotation broadcast using FastAPI WebSocket.

Protocol (JSON messages):
  Client → Server:
    {"type": "join",       "consultation_id": "...", "user_id": "...", "role": "specialist"}
    {"type": "annotation", "consultation_id": "...", "data": {...}}
    {"type": "cursor",     "consultation_id": "...", "x": 0.1, "y": 0.2, "z": 0.3}
    {"type": "chat",       "consultation_id": "...", "message": "..."}
    {"type": "leave",      "consultation_id": "..."}

  Server → Clients:
    {"type": "annotation", "user_id": "...", "data": {...}}
    {"type": "cursor",     "user_id": "...", "x": ..., "y": ..., "z": ...}
    {"type": "chat",       "user_id": "...", "message": "...", "timestamp": "..."}
    {"type": "user_joined","user_id": "...", "role": "..."}
    {"type": "user_left",  "user_id": "..."}
"""
import json
from datetime import datetime
from typing import Dict, List
from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """
    Manages WebSocket connections grouped by consultation room.
    Thread-safe via asyncio single-threaded event loop.
    """

    def __init__(self):
        # consultation_id → list of (WebSocket, user_id, role)
        self.rooms: Dict[str, List[dict]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        consultation_id: str,
        user_id: str,
        role: str = "viewer",
    ):
        await websocket.accept()
        if consultation_id not in self.rooms:
            self.rooms[consultation_id] = []

        conn = {"ws": websocket, "user_id": user_id, "role": role, "joined_at": datetime.utcnow().isoformat()}
        self.rooms[consultation_id].append(conn)

        # Notify others
        await self.broadcast(
            consultation_id,
            {"type": "user_joined", "user_id": user_id, "role": role},
            exclude_user=None,
        )
        logger.info(f"[WS] User {user_id} joined consultation {consultation_id}")

    async def disconnect(self, websocket: WebSocket, consultation_id: str, user_id: str):
        if consultation_id in self.rooms:
            self.rooms[consultation_id] = [
                c for c in self.rooms[consultation_id] if c["ws"] != websocket
            ]
            if not self.rooms[consultation_id]:
                del self.rooms[consultation_id]

        await self.broadcast(
            consultation_id,
            {"type": "user_left", "user_id": user_id},
            exclude_user=user_id,
        )
        logger.info(f"[WS] User {user_id} left consultation {consultation_id}")

    async def broadcast(
        self,
        consultation_id: str,
        message: dict,
        exclude_user: str = None,
    ):
        """Send message to all users in a consultation room."""
        if consultation_id not in self.rooms:
            return

        dead_connections = []
        for conn in self.rooms[consultation_id]:
            if exclude_user and conn["user_id"] == exclude_user:
                continue
            try:
                await conn["ws"].send_text(json.dumps(message))
            except Exception:
                dead_connections.append(conn)

        # Clean up dead connections
        for conn in dead_connections:
            self.rooms[consultation_id] = [
                c for c in self.rooms[consultation_id] if c != conn
            ]

    async def send_to_user(self, consultation_id: str, user_id: str, message: dict):
        """Send a message to a specific user in the room."""
        if consultation_id not in self.rooms:
            return
        for conn in self.rooms[consultation_id]:
            if conn["user_id"] == user_id:
                try:
                    await conn["ws"].send_text(json.dumps(message))
                except Exception:
                    pass

    def get_room_users(self, consultation_id: str) -> List[dict]:
        """Return list of connected users in a room."""
        if consultation_id not in self.rooms:
            return []
        return [
            {"user_id": c["user_id"], "role": c["role"], "joined_at": c["joined_at"]}
            for c in self.rooms[consultation_id]
        ]

    def room_count(self, consultation_id: str) -> int:
        return len(self.rooms.get(consultation_id, []))


# Global singleton
ws_manager = ConnectionManager()
