# Testing de los endpoints
# Falta testear Admin

from DB.database import get_session
from fastapi.testclient import TestClient
from prueba import app
from sqlmodel import SQLModel, create_engine, Session
import pytest
import os
import errno

# Crea la BD, cierra las conexiones y elimina la BD
@pytest.fixture(scope="session")
def test_db():
    # Crear la base de datos de prueba
    engine = create_engine("sqlite:///./test/test.db")
    SQLModel.metadata.create_all(engine)
    yield engine
    # Cerrar todas las conexiones del engine
    engine.dispose()
    # Eliminar la base de datos después de las pruebas
    try:
        os.remove("./test/test.db")
    except OSError as e:
        if e.errno != errno.ENOENT:  # Ignorar si el archivo no existe
            raise

# Crea la session
@pytest.fixture
def test_session(test_db):
    session = Session(test_db)
    try:
        yield session
    finally:
        session.close()

# Modifica la API para hacer consultas en BD de Testing
@pytest.fixture
def client(test_session):
    app.dependency_overrides[get_session] = lambda: test_session
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_read_main(client):
    response = client.get("/")  # Suponiendo que tienes una ruta en la raíz
    assert response.status_code == 200
    assert response.json() == {"messaje":"Bienvenido! Mira todas las tareas pendientes."}

# Creacion de usuario
@pytest.mark.users_testing
def test_create_user(client):
    response = client.post("/users/", json={"username": "test", "email": "test@test.com", "password":"5555", "role":"admin"})
    assert response.status_code == 202
    assert response.json() == {"detail" : "Se creo un nuevo usuario."}

@pytest.mark.users_testing
def test_failed_create_user(client):
    response = client.post("/users/", json={"username": "test", "email": "test@test.com", "password":"5555"})
    assert response.status_code == 406
    assert response.json() == {"detail":"Ya existe un usuario con este username"}

    response = client.post("/users/", json={"username": "testing", "email": "test@test.com", "password":"5555"})
    assert response.status_code == 406
    assert response.json() == {"detail":"Ya existe un usuario con este email"}

# Login de usuario
@pytest.fixture
def auth_headers(client):
    login_data = {"username": "test", "password": "5555"}  # Credenciales
    response = client.post("/login", data=login_data)  # OAuth usa 'data'
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Lectura de los usuarios
@pytest.mark.users_testing
def test_get_user_me(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    user_data = response.json()
    assert all(key in user_data for key in ["username","email","user_id"])
    assert response.json() == {"username": "test", "email":"test@test.com", "user_id":1}

@pytest.mark.users_testing
def test_get_user_all(client, auth_headers):
    response = client.get("/users/all-users/", headers=auth_headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    for user in users:
        assert all(key in user for key in ["username","email","user_id"])

@pytest.mark.users_testing
def test_get_user_by_username(client, auth_headers):
    response = client.get("/users/all-users/", headers=auth_headers, params={"username":"test"})
    assert response.status_code == 200
    assert response.json() == {"username": "test", "email":"test@test.com", "user_id":1}

@pytest.mark.users_testing
def test_failed_get_user_all(client, auth_headers):
    response = client.get("/users/all-users/", headers=auth_headers, params={"username":"mirko_dev"})
    assert response.status_code == 404
    assert response.json() == {"detail":"User no encontrado"}

@pytest.mark.users_testing
def test_get_user_id(client, auth_headers):
    response = client.get("/users/1", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"username": "test", "email":"test@test.com", "user_id":1}

@pytest.mark.users_testing
def test_failed_get_user_id(client, auth_headers):
    response = client.get("/users/10000", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail":"No se ha encontrado el usario"}

# Creacion, lectura y modificacion de task
@pytest.mark.tasks_testing
def test_create_task(client, auth_headers):
    response = client.post("/tasks", headers=auth_headers, json={"text":"testing", "user_id":1})
    assert response.status_code == 201
    assert response.json() == {"detail": "Se creó una nueva tarea."}

@pytest.mark.tasks_testing
def test_get_tasks(client, auth_headers):
    response = client.get("/tasks/", headers=auth_headers)
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    for user in tasks:
        assert all(key in user for key in ["text","id","category", "tags", "user_id"])

@pytest.mark.tasks_testing
def test_update_task(client, auth_headers):
    response = client.patch(f"/tasks/{1}", headers=auth_headers, json={"text":"testing de update", "category":"Test", "tags":["probando","olvidalo"]})
    assert response.status_code == 202
    assert response.json() == {"detail": "Tarea actualizada con éxito"}

@pytest.mark.tasks_testing
def test_failed_update_task(client, auth_headers):
    response = client.patch(f"/tasks/{10000}", headers=auth_headers, json={"text":"testing de update", "category":"Test", "tags":["probando","olvidalo"]})
    assert response.status_code == 404
    assert response.json() == {"detail": "No se encontró la tarea."}

# Eliminacion de task
@pytest.mark.tasks_testing
def test_delete_task(client, auth_headers):
    response = client.delete("/tasks/1", headers=auth_headers)
    assert response.status_code == 202
    assert response.json() == {"detail": "Tarea eliminada exitosamente"}

@pytest.mark.tasks_testing
def test_failed_delete_task(client, auth_headers):
    response = client.delete("/tasks/100000", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "No se encontró la tarea."}

# Eliminacion de usuario
@pytest.mark.users_testing
def test_delete_user(client, auth_headers):
    response = client.delete("/users/me", headers=auth_headers)
    assert response.status_code == 202
    assert response.json() == {"detail":"Usuario eliminado con éxito."}

"""@pytest.mark.admin_testing
def test_admin(client, auth_headers):
    response = client.get("users/admin/1", headers=auth_headers)
    print(response.json())
    assert response.status_code == 200
    assert response.json() == {"user_id":1,"username": "test", "email":"test@test.com", "disabled":False,"role":"admin"}"""