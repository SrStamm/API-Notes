# Crear una API de tareas pendientes

from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import Response, JSONResponse
from routers import task, users, auth
from DB.database import Session, engine, create_db_and_tables

# Inicializa la app
app = FastAPI(
    title="API de Notas",
    description="Esta API realiza un CRUD sobre notas y usuarios, con autenticacion y donde cada usuario puede tener sus propias notas"
)

try:
    # Inicializa la base de datos
    create_db_and_tables()
    print("Base de Datos y tablas creadas con exito")
except:
    print({"error":"No se pudo conectar con la base de datos"})

# Routers
app.include_router(task.router)
app.include_router(users.router)
app.include_router(auth.router)

@app.middleware(middleware_type='http')
async def global_error_handler(request : Request, call_next):
    print("Middleware is running!")
    try:
            response = await call_next(request)
            return response
    except Exception as exc: # Capturar cualquier otra excepción no manejada
        print(f"ERROR NO MANEJADO en la petición: {request.method} {request.url} - Error: {exc}") # LOGGING centralizado de errores no manejados (IMPORTANTE)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"type": "ServerError", "message": "Error interno del servidor no esperado"}}, # Formato JSON consistente
        )

# Base
@app.get("/")
def root():
    return {"Bienvenido! Mira todas las tareas pendientes."}