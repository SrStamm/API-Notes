from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from Models.ws import manager

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Mantener la conexión abierta
            data = await websocket.receive_text()
            # Puedes manejar mensajes del cliente si es necesario
    except WebSocketDisconnect:
        manager.disconnect(user_id)