from fastapi.testclient import TestClient
from prueba import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"messaje":"Bienvenido! Mira todas las tareas pendientes."}

def get_auth_token():
    login_data = {"username": "mirko_dev", "password": "123456"}  # Asegúrate de usar credenciales correctas
    response = client.post("/login", data=login_data)  # OAuth usa 'data', no 'json'
    assert response.status_code == 200, response.json()
    return response.json()["access_token"]

def test_get_task_me():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/tasks/", headers=headers)
    # assert response.status_code == 200

    tasks = response.json()
    assert isinstance(tasks, list)

    for task in tasks:
        assert "text" in task

def test_get_task_all():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/tasks/all", headers=headers)
    # assert response.status_code == 200

    tasks = response.json()
    assert isinstance(tasks, list)

    for task in tasks:
        assert "id" in task
        assert "text" in task
        assert "user_id" in task

def test_get_task_id():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/tasks/1", headers=headers)
    assert response.status_code == 202

    task = response.json()
    assert task == {"text": "nota"}

def test_failed_get_task_id_():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/tasks/10000000", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail":"No se encontró la tarea."}

def test_create_task():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/tasks/", headers=headers, json={"text":"texto de prueba de creacion"})
    assert response.status_code == 201
    assert response.json() == {"detail": "Se creó una nueva tarea."}

def test_failed_create_task():
    response = client.post("/tasks/")
    assert response.status_code == 401
    assert response.json() == {"detail":"Not authenticated"}

def test_update_task():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put("/tasks/5", headers=headers, json={"id":5,"text":"texto de prueba de actualizacion"})
    # assert response.status_code == 202
    assert response.json() == {"detail": "Tarea actualizada con éxito"}

def test_failed_update_task():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put("/tasks/666666", headers=headers, json={"id":6666666,"text":"texto de prueba de actualizacion"})
    assert response.status_code == 404
    assert response.json() == {"detail": "No se encontró la tarea."}

def test_delete_task():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/tasks/13", headers=headers)
    assert response.status_code == 204

def test_failed_delete_task():
    return