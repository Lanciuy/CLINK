from fastapi import WebSocket
from typing import List
import json

class WebSocketManager:
    """Real-time download progress and speed broadcaster."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_progress(self, progress_data: dict):
        """Broadcasts progress dict to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(progress_data))
            except Exception:
                disconnected.append(connection)
                
        for conn in disconnected:
            self.disconnect(conn)
