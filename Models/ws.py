from fastapi import WebSocket
from fastapi.websockets import WebSocketState
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    # Conecta el usuario
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    # Desconecta al usuario
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    # Envia un mensaje personal a un usuario objetivo
    async def send_personal_message(self, message: str, user_id: int):
        # Busca en los usuarios activos
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(message)

# Instancia global que compartirán todos los routers
manager = ConnectionManager()