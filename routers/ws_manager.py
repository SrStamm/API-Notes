from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from routers.auth import current_user
from Models.ws import manager
from Models.db_models import Users

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, user: Users = Depends(current_user)):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Mantener la conexión abierta
            data = await websocket.receive_text()
            # Puedes manejar mensajes del cliente si es necesario
    except WebSocketDisconnect:
        manager.disconnect(user_id)