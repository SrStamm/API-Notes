# Crear una API de tareas pendientes

from fastapi import FastAPI
from routers import task, users, auth
from DB.database import Session, engine, create_db_and_tables

# Inicializa la app
app = FastAPI(
    title="API de Notas",
    description="Esta API realiza un CRUD sobre notas y usuarios, con autenticacion y donde cada usuario puede tener sus propias notas"
)

# Inicializa la base de datos
create_db_and_tables()

# Routers
app.include_router(task.router)
app.include_router(users.router)
app.include_router(auth.router)

# Base
@app.get("/")
def root():
    return {"Bienvenido! Mira todas las tareas pendientes."}