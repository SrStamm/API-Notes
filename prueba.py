import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routers import notes, users, auth
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En desarrollo puedes usar "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)