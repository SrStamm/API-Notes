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

def test_get_user_me():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)  
    assert response.status_code == 200, response.json()
    assert response.json() == {"username": "mirko_dev", "email": "mirko@dev.com", "user_id": 1}

def test_get_user_all():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/users/all", headers=headers)
    assert response.status_code == 200

    users = response.json()
    assert isinstance(users, list)
    
    for user in users:
        assert "user_id" in user
        assert "username" in user
        assert "email" in user