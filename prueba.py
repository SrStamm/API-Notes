# Crear una API de tareas pendientes

from fastapi import FastAPI
from routers import task, users, auth

# Inicializa la app
app = FastAPI()

# Routers
app.include_router(task.router)
app.include_router(users.router)
app.include_router(auth.router)

# Base
@app.get("/")
def root():
    return {"Bienvenido! Mira todas las tareas pendientes."}
    