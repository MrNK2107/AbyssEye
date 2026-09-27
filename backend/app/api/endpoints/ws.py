from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/live-stream")
async def websocket_live_stream(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Initial greeting event
        await websocket.send_json({
            "event_type": "STREAM_CONNECTED",
            "message": "Connected to ABYSSEYE Real-Time Sonar Evidence Broadcaster"
        })
        while True:
            # Keep connection alive & receive client acknowledgments
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
