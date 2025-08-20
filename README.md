# 📝 API Notes

API REST para gestionar notas con autenticación y autorización, desarrollada con **FastAPI** y **PostgreSQL**.

## 🚀 Características
- Registro e inicio de sesión de usuarios (con **JWT**).
- CRUD de notas (crear, leer, actualizar, eliminar).
- Categorías y etiquetas para cada nota.
- Compartir notas con otros usuarios.
- Gestión de sesiones activas y cierre de sesión.
- Roles básicos (usuario normal, admin).
- Documentación automática en `/docs`.

## 🛠️ Tecnologías utilizadas
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [JWT - OAuth2](https://jwt.io/)
- [Docker](https://www.docker.com/) (para despliegue local)

## 📦 Instalación y uso

### 1. Clonar el repositorio
```bash
git clone https://github.com/SrStamm/API-Notes.git
cd API-Notes
```
### 2. Archivo .env
El repositorio cuenta con un `.env` que se debe llenar con los datos de containers de Docker de Redis y Postgres
```bash
TESTING='False'
TESTING_DATABASE_URL=

DATABASE_URL=

HOST_REDIS=
PORT_REDIS=
```

### 3. Levantar servicios
```bash
dcoker-compose up
```

### 4. Acceder a la API
API base: `http://localhost:8000`
Documentación: `http://localhost:8000/redoc` o `http://localhost:8000/docs`

### 5. Tests
Se debe ejecutar el bash script
```bash
script-test.sh
```

## 🌐 Frontend

El frontend de este proyecto se encuentra en:
👉 Notes-Frontend

## 📌 Estado del proyecto

✅ Proyecto básico terminado.
Este repo demuestra un CRUD completo con FastAPI y autenticación.
El siguiente paso fue el desarrollo del frontend en un repositorio separado.
