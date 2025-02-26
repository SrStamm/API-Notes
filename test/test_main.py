from fastapi.testclient import TestClient
import pytest
from prueba import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"messaje":"Bienvenido! Mira todas las tareas pendientes."}

@pytest.fixture
def auth_headers():
    login_data = {"username": "mirko_dev", "password": "123456"}  # Credenciales
    response = client.post("/login", data=login_data)  # OAuth usa 'data'
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_user_me(auth_headers):
    response = client.get("/users/me", headers=auth_headers)  
    assert response.status_code == 200
    user_data = response.json()
    assert all(key in user_data for key in ["username","email","user_id"])
    assert response.json() == {"username": "mirko_dev", "email":"mirko@dev.com", "user_id":1}

def test_get_user_all(auth_headers):
    response = client.get("/users/", headers=auth_headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)    
    for user in users:
        assert all(key in user for key in ["username","email","user_id"])

def test_get_task_me(auth_headers):
    response = client.get("/tasks/", headers=auth_headers)
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    for task in tasks:
        assert "text" in task

def test_get_task_all(auth_headers):
    response = client.get("/tasks/all", headers=auth_headers)
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    for task in tasks:
        assert all(key in task for key in ["id","text","user_id"])

def test_get_task_id(auth_headers):
    response = client.get("/tasks/5", headers=auth_headers)
    assert response.status_code == 202
    task = response.json()
    assert "text" in task

def test_failed_get_task_id(auth_headers):
    response = client.get("/tasks/10000000", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail":"No se encontró la tarea."}

def test_create_task(auth_headers):
    response = client.post("/tasks/", headers=auth_headers, json={"text":"Nueva tarea"})
    assert response.status_code == 201
    assert response.json() == {"detail": "Se creó una nueva tarea."}

def test_failed_create_task():
    response = client.post("/tasks/")
    assert response.status_code == 401
    assert response.json() == {"detail":"Not authenticated"}

def test_update_task(auth_headers):
    response = client.put("/tasks/5", headers=auth_headers, json={"text":"Actualizacion", "category":"Test"})
    assert response.status_code == 202
    assert response.json() == {"detail": "Tarea actualizada con éxito"}

def test_failed_update_task(auth_headers):
    response = client.put("/tasks/666666", headers=auth_headers, json={"id":6666666,"text":"Error"})
    assert response.status_code == 404
    assert response.json() == {"detail": "No se encontró la tarea."}

"""def test_delete_task(auth_headers):
    response = client.delete("/tasks/12", headers=auth_headers)
    assert response.status_code == 204"""

def test_failed_delete_task(auth_headers):
    response = client.delete("/tasks/10000", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail":"No se encontró la tarea."}