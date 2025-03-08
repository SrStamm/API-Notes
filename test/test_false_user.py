from fastapi.testclient import TestClient
import pytest
from prueba import app

client = TestClient(app)

@pytest.fixture
def auth_headers():
    login_data = {"username": "falso_dev", "password": "0000"}  # Credenciales
    response = client.post("/login", data=login_data)  # OAuth usa 'data'
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_user_me(auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"user_id":15, "username":"falso_dev", "email":"falsisimo@email.com"}

def test_patch_user(auth_headers):
    response = client.patch("/users/me", headers=auth_headers, json={"username":"falso_dev"})  
    assert response.status_code == 202
    assert response.json() == {"detail":"Usuario actualizado con exito"}

def test_create_task(auth_headers):
    response = client.post("/tasks/", headers=auth_headers, json={"text":"probando testing"})
    assert response.status_code == 201
    assert response.json() == {"detail": "Se creó una nueva tarea."}

def test_update_task(auth_headers):
    response = client.patch("/tasks/32", headers=auth_headers, json={"tags" : ["probando el","testing"]})
    assert response.status_code == 202
    assert response.json() == {"detail": "Tarea actualizada con éxito"}

def test_delete_task(auth_headers):
    response = client.delete("/tasks/34", headers=auth_headers)
    assert response.status_code == 204