from DB.database import get_session
from fastapi.testclient import TestClient
from prueba import app
from sqlmodel import SQLModel, create_engine, Session
import pytest

# Crear la base de datos de prueba y las tablas necesarias
engine = create_engine("sqlite:///./test/test.db")
SQLModel.metadata.create_all(engine)

def get_test_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

# Sobrescribe la dependencia get_session
app.dependency_overrides[get_session] = get_test_session

client = TestClient(app)

def test_read_main():
    response = client.get("/")  # Suponiendo que tienes una ruta en la raíz
    assert response.status_code == 200
    assert response.json() == {"messaje":"Bienvenido! Mira todas las tareas pendientes."}

def test_create_user():
    response = client.post("/users/", json={"username": "test", "email": "test@test.com", "password":"5555"})
    assert response.status_code == 202
    assert response.json() == {"detail" : "Se creo un nuevo usuario."}

def test_failed_create_user():
    response = client.post("/users/", json={"username": "test", "email": "test@test.com", "password":"5555"})
    assert response.status_code == 406
    assert response.json() == {"detail":{"error" : "Ya existe un usuario con este username"}}

    response = client.post("/users/", json={"username": "testing", "email": "test@test.com", "password":"5555"})
    assert response.status_code == 406
    assert response.json() == {"detail":{"error" : "Ya existe un usuario con este email"}}

@pytest.fixture
def auth_headers():
    login_data = {"username": "test", "password": "5555"}  # Credenciales
    response = client.post("/login", data=login_data)  # OAuth usa 'data'
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_user_me(auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    user_data = response.json()
    assert all(key in user_data for key in ["username","email","user_id"])
    assert response.json() == {"username": "test", "email":"test@test.com", "user_id":1}

def test_get_user_all(auth_headers):
    response = client.get("/users/all-users/", headers=auth_headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    for user in users:
        assert all(key in user for key in ["username","email","user_id"])

def test_get_user_id(auth_headers):
    response = client.get("/users/1", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"username": "test", "email":"test@test.com", "user_id":1}