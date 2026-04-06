"""WebSocket endpoint for live simulation streaming."""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from loguru import logger

from app.core.supabase import get_supabase_client
from app.services.ws_manager import ws_manager

router = APIRouter()


@router.websocket("/ws/simulation/{sim_id}")
async def simulation_stream(
    websocket: WebSocket,
    sim_id: str,
    token: str = Query(default=""),
) -> None:
    """WebSocket endpoint for real-time simulation events.

    Connect with: ws://host/ws/simulation/{sim_id}?token=JWT
    """
    # Authenticate via JWT
    user_id = await _authenticate(websocket, token)
    if not user_id:
        return

    # Register client
    client = await ws_manager.connect(sim_id, websocket, user_id)

    try:
        # Keep connection alive — listen for client messages
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket error for sim {sim_id}: {e}")
    finally:
        await ws_manager.disconnect(sim_id, client)


async def _authenticate(websocket: WebSocket, token: str) -> str | None:
    """Validate JWT token and return user_id, or close with 4001."""
    if not token:
        await websocket.close(code=4001, reason="Token fehlt")
        return None

    try:
        supabase = get_supabase_client()
        response = supabase.auth.get_user(token)
        if response.user is None:
            await websocket.close(code=4001, reason="Ungültiger Token")
            return None
        return response.user.id
    except Exception as e:
        logger.warning(f"WS auth failed: {e}")
        await websocket.close(code=4001, reason="Authentifizierung fehlgeschlagen")
        return None
