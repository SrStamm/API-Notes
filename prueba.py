from sqlalchemy import true
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from routers import notes, users, auth, ws_manager
from DB.database import create_db_and_tables
import logging

# Configurar logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Inicializa la app
app = FastAPI(
    title="API de Notas",
    description="Esta API realiza un CRUD sobre notas y usuarios, con autenticacion y donde cada usuario puede tener sus propias notas"
)

from fastapi.middleware.cors import CORSMiddleware
# Configuración CORS más flexible para desarrollo
origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los headers
    expose_headers=["*"]  # Expone todos los headers
)

try:
    # Inicializa la base de datos
    create_db_and_tables()
    print("Base de Datos y tablas creadas con exito")
except:
    print({"error":"No se pudo conectar con la base de datos"})

# Routers
app.include_router(notes.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(ws_manager.router)

# Base
@app.get("/", include_in_schema=False, status_code=200)
def root():
    return {"messaje":"Bienvenido! Mira todas las tareas pendientes."}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )

"""
@app.websocket("/ws")
async def websocket_endpoint(websocket : WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f'Message text was: {data}')
        await websocket.receive_text()
"""


"""from Models.ws import ConnectionManager
manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Received:{data}", websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.send_personal_message("Bye!!!",websocket)"""