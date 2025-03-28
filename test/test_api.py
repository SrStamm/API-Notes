# Testing de los endpoints
# Falta testear Admin
# Falta testear Autorizacion

from Models.db_models import Users, Notes
from DB.database import get_session
from fastapi.testclient import TestClient
from prueba import app
from sqlmodel import SQLModel, create_engine, Session
import pytest, os, errno
from datetime import date

# Crea la BD, cierra las conexiones y elimina la BD
engine = create_engine("sqlite:///./test/test.db")
@pytest.fixture(scope="session")
def test_db():
    # Crear la base de datos de prueba
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
    response = client.post("/users/", json={"username": "test", "email": "test@test.com", "password":"5555"})
    assert response.status_code == 202
    assert response.json() == {"detail" : "Se creo un nuevo usuario."}

    response = client.post("/users/", json={"username": "f", "email": "f@test.com", "password":"00000"})
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

def test_login(client):
    login_data = {"username": "test", "password": "5555"}  # Credenciales
    response = client.post("/login", data=login_data)
    assert response.status_code == 200

def test_failed_login(client):
    response = client.post("/login", data={"username": "falla", "password": "error"})
    assert response.status_code == 404
    assert response.json() == {"detail":"Usuario no encontrado o no existe"}

    response = client.post("/login", data={"username": "test", "password": "error"})
    assert response.status_code == 400
    assert response.json() == {"detail":"Contraseña incorrecta"}

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
    assert all(key in user_data for key in ["username","user_id"])
    assert response.json() == {"username": "test", "user_id":1}

@pytest.mark.users_testing
def test_get_user_all(client, auth_headers):
    response = client.get("/users/all-users/", headers=auth_headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    for user in users:
        assert all(key in user for key in ["username","user_id"])

@pytest.mark.users_testing
def test_get_user_by_username(client, auth_headers):
    response = client.get("/users/all-users/", headers=auth_headers, params={"username":"test"})
    assert response.status_code == 200
    assert response.json() == {"username": "test", "user_id":1}

@pytest.mark.users_testing
def test_failed_get_user_all(client, auth_headers):
    response = client.get("/users/all-users/", headers=auth_headers, params={"username":"mirko_dev"})
    assert response.status_code == 404
    assert response.json() == {"detail":"User no encontrado"}

@pytest.mark.users_testing
def test_get_user_id(client, auth_headers):
    response = client.get("/users/1", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"username": "test", "user_id":1}

@pytest.mark.users_testing
def test_failed_get_user_id(client, auth_headers):
    response = client.get("/users/10000", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail":"No se ha encontrado el usario"}

# Creacion, lectura y modificacion de note
@pytest.mark.notes_testing
def test_create_note(client, auth_headers):
    response = client.post("/notes/", headers=auth_headers, json={"text":"testing"})
    assert response.status_code == 201
    assert response.json() == {"detail": "Se creó una nueva nota."}

@pytest.mark.notes_testing
def test_create_many_notes(client, auth_headers):
    response = client.post("/notes", headers=auth_headers, json={"text":"ojala, no?", "user_id":1})
    assert response.status_code == 201
    assert response.json() == {"detail": "Se creó una nueva nota."}

    response = client.post("/notes", headers=auth_headers, json={"text":"vvlc", "user_id":1})
    assert response.status_code == 201
    assert response.json() == {"detail": "Se creó una nueva nota."}

    response = client.post("/notes", headers=auth_headers, json={"text":"sasaki", "user_id":1})
    assert response.status_code == 201
    assert response.json() == {"detail": "Se creó una nueva nota."}

    response = client.patch(f"/notes/{3}", headers=auth_headers, json={"category":"work", "tags":["cierrenlo"]})
    assert response.status_code == 202
    assert response.json() == {"detail": "Nota actualizada con éxito"}

    response = client.patch(f"/notes/{4}", headers=auth_headers, json={"category":"study", "tags":["Personaje"]})
    assert response.status_code == 202
    assert response.json() == {"detail": "Nota actualizada con éxito"}

@pytest.mark.notes_testing
def test_get_notes_filtered(client, auth_headers):
    response = client.get('/notes/personal/', headers=auth_headers, params={'limit':2})
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    assert len(notes) == 2

    response = client.get('/notes/personal/', headers=auth_headers, params={'category_searched':'work'})
    assert response.status_code == 200
    assert response.json() == [{'id': 3, 'text': 'vvlc', 'category': 'work', 'tags': [{'tag': 'cierrenlo'}], 'user_id': 1}]

@pytest.mark.notes_testing
def test_get_notes(client, auth_headers):
    response = client.get("/notes/personal/", headers=auth_headers)
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    for user in notes:
        assert all(key in user for key in ["text","id","category", "tags", "user_id"])

@pytest.mark.notes_testing
def test_update_note(client, auth_headers):
    response = client.patch(f"/notes/{1}", headers=auth_headers, json={"text":"testing de update", "category":"study", "tags":["probando","olvidalo"]})
    assert response.status_code == 202
    assert response.json() == {"detail": "Nota actualizada con éxito"}

@pytest.mark.notes_testing
def test_failed_update_note(client, auth_headers):
    response = client.patch(f"/notes/{10000}", headers=auth_headers, json={"text":"testing de update", "category":"Test", "tags":["probando","olvidalo"]})
    assert response.status_code == 404
    assert response.json() == {"detail": "No se encontró la nota."}

# Eliminacion de note
@pytest.mark.notes_testing
def test_delete_note(client, auth_headers):
    response = client.delete("/notes/1", headers=auth_headers)
    assert response.status_code == 202
    assert response.json() == {"detail": "Nota eliminada exitosamente"}

@pytest.mark.notes_testing
def test_failed_delete_note(client, auth_headers):
    response = client.delete("/notes/100000", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "No se encontró la nota."}

@pytest.mark.users_testing
# Actualizacion del usuario
def test_patch_user(client, auth_headers):
    response = client.patch("/users/me", headers=auth_headers, json={"username": "testing", "password": "0000", "email":"cambio@email.com"})
    assert response.status_code == 202
    assert response.json() == {"detail":"Usuario actualizado con exito"}

# Login de usuario post update
@pytest.fixture
def auth_headers2(client):
    login_data = {"username": "testing", "password": "0000"}  # Credenciales
    response = client.post("/login", data=login_data)  # OAuth usa 'data'
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Eliminacion de usuario
@pytest.mark.users_testing
def test_delete_actual_user(client, auth_headers2):
    response = client.delete("/users/me", headers=auth_headers2)
    assert response.status_code == 202
    assert response.json() == {"detail":"Usuario eliminado con éxito."}

@pytest.mark.admin_testing
def test_create_admin_user(client):
    response = client.post("/users/", json={"username": "admin", "email": "admin@email.com", "password":"admin"})
    assert response.status_code == 202
    
    session = Session(engine)
    # Crear un usuario normal
    user_found = session.get(Users, 3)
    user_found.role = 'ADMIN'
    session.commit()
    session.close()

@pytest.fixture
def auth_headers_admin(client):

    login_data = {"username": "admin", "password": "admin"}  # Credenciales
    response = client.post("/login", data=login_data)  # OAuth usa 'data'
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.admin_testing
def test_get_user_admin(client, auth_headers_admin):
    response = client.get("/users/admin/2", headers=auth_headers_admin)
    assert response.status_code == 200
    assert response.json() == {'user_id' : 2, "username": "f", "email": "f@test.com", 'disabled': False, 'role': 'user'}

@pytest.mark.admin_testing
def test_put_user_admin(client, auth_headers_admin):
    response = client.put("/users/admin/2", headers=auth_headers_admin, json={"username": "cambiado", "password": "1111", "email":"cambio@email.com"})
    assert response.status_code == 202
    assert response.json() == {"detail":"El usuario fue actualizado"}

@pytest.mark.admin_testing
def test_failed_put_user_admin(client, auth_headers_admin):
    response = client.put("/users/admin/10000", headers=auth_headers_admin, json={"username": "cambiado", "password": "1111", "email":"cambio@email.com"})
    assert response.status_code == 404
    assert response.json() == {"detail":"No se ha encontrado el usario"}

@pytest.mark.admin_testing
def test_delete_user_admin(client, auth_headers_admin):
    response = client.post("/users/", headers=auth_headers_admin, json={"username": "eliminado", "email": "eli@minado.com", "password":"delete", "role":"user"})
    assert response.status_code == 202
    assert response.json() == {"detail" : "Se creo un nuevo usuario."}

    response = client.delete("/users/admin/2", headers=auth_headers_admin)
    assert response.status_code == 204

@pytest.mark.admin_testing
def test_failed_delete_user_admin(client, auth_headers_admin):
    response = client.delete("/users/admin/10000", headers=auth_headers_admin)
    assert response.status_code == 404
    assert response.json() == {"detail":"No se ha encontrado el usario"}

@pytest.mark.admin_testing
def test_create_many_notes_2(client, auth_headers_admin):
    response = client.post("/notes", headers=auth_headers_admin, json={"text":"ojala, no?", "user_id":1})
    assert response.status_code == 201
    assert response.json() == {"detail": "Se creó una nueva nota."}

    response = client.post("/notes", headers=auth_headers_admin, json={"text":"vvlc", "user_id":1})
    assert response.status_code == 201
    assert response.json() == {"detail": "Se creó una nueva nota."}

    response = client.post("/notes", headers=auth_headers_admin, json={"text":"sasaki", "user_id":1})
    assert response.status_code == 201
    assert response.json() == {"detail": "Se creó una nueva nota."}

@pytest.mark.admin_testing
def test_get_notes_admin(client, auth_headers_admin):
    response = client.get("/notes/admin/all/", headers=auth_headers_admin)
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    for user in notes:
        assert all(key in user for key in ["text","id","category", "tags", "user_id", "create_date"])

    response = client.get("/notes/admin/all/", headers=auth_headers_admin, params={"limit":2, "order_by_date":"asc"})
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    assert len(notes) == 2

@pytest.mark.admin_testing
def test_get_notes_admin_by_id(client, auth_headers_admin):
    response = client.get("/notes/admin/1", headers=auth_headers_admin)
    assert response.status_code == 200
    assert response.json() == {"text":"ojala, no?", "user_id":1, "category":"unknown", "user_id":3, "id":1, "tags":[]}

@pytest.mark.admin_testing
def test_failed_get_notes_admin_by_id(client, auth_headers_admin):
    response = client.get("/notes/admin/666666", headers=auth_headers_admin)
    assert response.status_code == 404
    assert response.json() == {"detail": "No se encontró la nota."}

@pytest.mark.admin_testing
def test_delete_notes_admin(client, auth_headers_admin):
    response = client.delete("/notes/admin/1", headers=auth_headers_admin)
    assert response.status_code == 202
    assert response.json() == {"detail": "Nota eliminada exitosamente"}

@pytest.mark.admin_testing
def test_failed_delete_notes_admin(client, auth_headers_admin):
    response = client.delete("/notes/admin/6666666", headers=auth_headers_admin)
    assert response.status_code == 404
    assert response.json() == {"detail": "No se encontró la nota."}

@pytest.mark.auth_testing
def test_user_disabled(client, auth_headers_admin):
    response = client.put("/users/admin/4", headers=auth_headers_admin, json={"username": "fallara", "password": "0000", "email":"cambio@email.com", 'disabled':True})
    assert response.status_code == 202
    assert response.json() == {"detail":"El usuario fue actualizado"}

    login_data = {"username": "fallara", "password": "0000"}
    response = client.post("/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    header = {"Authorization": f"Bearer {token}"}

    response = client.post('/notes/', headers=header, json={'text':'inactivo'})
    response.status_code == 400
    response.json() == {'detail':'Usuario inactivo'}
