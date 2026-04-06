"""WebSocket connection manager for live simulation streaming.

Manages WebSocket connections grouped by simulation ID.
Each client gets a dedicated send queue so slow clients
never block the simulation event loop.
"""

import asyncio
import contextlib

from fastapi import WebSocket
from loguru import logger

CLIENT_QUEUE_MAX = 256
SEND_TIMEOUT_S = 5.0


class ConnectedClient:
    """A single WebSocket client with its own send queue."""

    def __init__(self, websocket: WebSocket, user_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.queue: asyncio.Queue[str] = asyncio.Queue(maxsize=CLIENT_QUEUE_MAX)
        self._send_task: asyncio.Task | None = None

    def start_send_loop(self) -> None:
        """Start the background task that drains the queue and sends via WS."""
        self._send_task = asyncio.create_task(self._send_loop())

    async def stop(self) -> None:
        """Cancel the send loop."""
        if self._send_task and not self._send_task.done():
            self._send_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._send_task

    async def _send_loop(self) -> None:
        """Background task: drain queue → send to WebSocket."""
        try:
            while True:
                message = await self.queue.get()
                try:
                    await asyncio.wait_for(
                        self.websocket.send_text(message),
                        timeout=SEND_TIMEOUT_S,
                    )
                except (TimeoutError, Exception):
                    logger.warning("Send failed, closing slow client")
                    break
        except asyncio.CancelledError:
            pass


class ConnectionManager:
    """Manages WebSocket connections grouped by simulation ID."""

    def __init__(self) -> None:
        self._connections: dict[str, set[ConnectedClient]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, sim_id: str, websocket: WebSocket, user_id: str) -> ConnectedClient:
        """Accept a WebSocket connection and register the client."""
        await websocket.accept()
        client = ConnectedClient(websocket, user_id)
        client.start_send_loop()

        async with self._lock:
            if sim_id not in self._connections:
                self._connections[sim_id] = set()
            self._connections[sim_id].add(client)

        logger.info(f"WS client connected to sim {sim_id} (total: {len(self._connections[sim_id])})")
        return client

    async def disconnect(self, sim_id: str, client: ConnectedClient) -> None:
        """Remove a client from the connection pool."""
        await client.stop()

        async with self._lock:
            clients = self._connections.get(sim_id)
            if clients:
                clients.discard(client)
                if not clients:
                    del self._connections[sim_id]

        logger.info(f"WS client disconnected from sim {sim_id}")

    async def broadcast(self, sim_id: str, message: str) -> None:
        """Send a message to all clients watching a simulation.

        If a client's queue is full (slow client), drops the oldest message.
        """
        async with self._lock:
            clients = self._connections.get(sim_id, set()).copy()

        for client in clients:
            try:
                client.queue.put_nowait(message)
            except asyncio.QueueFull:
                # Drop oldest, enqueue new
                with contextlib.suppress(asyncio.QueueEmpty):
                    client.queue.get_nowait()
                with contextlib.suppress(asyncio.QueueFull):
                    client.queue.put_nowait(message)

    def get_client_count(self, sim_id: str) -> int:
        """Get number of connected clients for a simulation."""
        return len(self._connections.get(sim_id, set()))


# Singleton instance
ws_manager = ConnectionManager()
