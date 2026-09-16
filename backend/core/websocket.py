import asyncio
import logging
from fastapi import WebSocket

logger = logging.getLogger("leakguard.websocket")


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast a JSON message to all connected WebSocket clients."""
        disconnected = []
        # Iterate over a shallow copy to prevent concurrency issues
        for websocket in list(self.active_connections):
            try:
                await websocket.send_json(message)
            except Exception as error:
                logger.debug(f"Failed to send to client: {error}")
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)

    def broadcast_sync(self, message: dict):
        """Synchronously schedule a broadcast on the running event loop if available."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(message))
        except RuntimeError:
            # If no running loop in the current thread, ignore or log
            logger.warning("broadcast_sync called with no running event loop in thread.")


manager = ConnectionManager()