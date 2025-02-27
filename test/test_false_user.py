from fastapi.testclient import TestClient
import pytest
from prueba import app

client = TestClient(app)

"""def test_post_user():
    response = client.post("/users/", json={"username":"falso","email":"falso","password":"falso"})  
    assert response.status_code == 202
    assert response.json() == {"detail" : "Se creo un nuevo usuario."}"""

@pytest.fixture
def auth_headers():
    login_data = {"username": "falso", "password": "falso"}  # Credenciales
    response = client.post("/login", data=login_data)  # OAuth usa 'data'
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_patch_user(auth_headers):
    response = client.patch("/users/me", headers=auth_headers, json={"username":"falso_dev"})  
    assert response.status_code == 202
    assert response.json() == {"detail":"Usuario actualizado con exito"}

def test_user_me(auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"user_id":"4","username":"falso_dev","email":"falso"}