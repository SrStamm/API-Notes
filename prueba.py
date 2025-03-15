# Crear una API de tareas pendientes
import uvicorn
from fastapi import FastAPI
from routers import task, users, auth
from DB.database import create_db_and_tables

from fastapi_pagination import Page, add_pagination

# Inicializa la app
app = FastAPI(
    title="API de Notas",
    description="Esta API realiza un CRUD sobre notas y usuarios, con autenticacion y donde cada usuario puede tener sus propias notas"
)

add_pagination(app)

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

# Base
@app.get("/", include_in_schema=False)
def root():
    return {"messaje":"Bienvenido! Mira todas las tareas pendientes."}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)