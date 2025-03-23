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
@pytest.mark.parametrize(
    "username, email, password, expected_status_code, expected_detail",
    [
        ("test", "test@test.com", "5555", 202, "Se creo un nuevo usuario."),
        ("f", "f@test.com", "00000", 202, "Se creo un nuevo usuario."),
        ("alter", "alterado@test.com", "00000", 202, "Se creo un nuevo usuario."),
        ("test", "test@test.com", "5555", 406, "Ya existe un usuario con este username"),
        ("testing", "test@test.com", "5555", 406, "Ya existe un usuario con este email")
    ] 
)
def test_create_user(client, username, email, password, expected_status_code, expected_detail):
    response = client.post("/users/", json={"username": username, "email": email, "password":password})
    assert response.status_code == expected_status_code
    assert response.json().get("detail") == expected_detail

@pytest.mark.auth_testing
@pytest.mark.parametrize(
    "username, password, expected_status_code, get, expected_detail",
    [
        ("test", "5555", 200, "token_type", "bearer"),
        ("falla", "error", 404, "detail", "Usuario no encontrado o no existe"),
        ("test", "error", 400, "detail", "Contraseña incorrecta")
    ]
)
def test_login(client, username, password, get, expected_status_code, expected_detail):
    login_data = {"username": username, "password": password}  # Credenciales
    response = client.post("/login", data=login_data)
    assert response.status_code == expected_status_code
    assert response.json().get(get) == expected_detail

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

@pytest.mark.notes_testing
@pytest.mark.parametrize (
        "text, expected_status, expected_detail",
        [
            ("testing", 201, "Se creó una nueva nota."),
            ("ojala, no", 201, "Se creó una nueva nota."),
            ("vvlc", 201, "Se creó una nueva nota."),
            ("sasaki", 201, "Se creó una nueva nota.")
        ]
)
def test_create_note(client, auth_headers, text, expected_status, expected_detail):
    response = client.post("/notes/", headers=auth_headers, json={"text":text})
    assert response.status_code == expected_status
    assert response.json().get("detail") == expected_detail

@pytest.mark.notes_testing
@pytest.mark.parametrize (
        "id, category, tags, expected_status, expected_detail",
        [
            (3, "work", ["cierrenlo"], 202, "Nota actualizada con éxito"),
            (4, "study", ["Personaje"], 202, "Nota actualizada con éxito"),
            (1, "study", ["probando","olvidalo"], 202, "Nota actualizada con éxito"),
            (10000, "study", ["probando","olvidalo"], 404, "No se encontró la nota.")
        ]
)
def test_path_notes(client, auth_headers, id, category, tags, expected_detail, expected_status):
    response = client.patch(f"/notes/{id}", headers=auth_headers, json={"category":category, "tags":tags})
    assert response.status_code == expected_status
    assert response.json().get("detail") == expected_detail

@pytest.mark.notes_testing
def test_get_notes_limited(client, auth_headers):
    response = client.get('/notes/', headers=auth_headers, params={'limit':2})
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    assert len(notes) == 2

@pytest.mark.notes_testing
@pytest.mark.parametrize(
    "query, param, status_expected, id, text, category, tag, user_id",
    [("category_searched", "work", 200, 3, "vvlc", "work", "cierrenlo", 1),
     ("search_text", "vvlc", 200, 3, "vvlc", "work", "cierrenlo", 1),
     ("tags_searched", "cierrenlo", 200, 3, "vvlc", "work", "cierrenlo", 1)
     ]
)
def test_get_notes_filtered(client, auth_headers, query, param, status_expected, id, text, category, tag, user_id):
    response = client.get('/notes/', headers=auth_headers, params={query:param})
    assert response.status_code == status_expected
    assert response.json() == [{'id': id, 'text': text, 'category': category, 'tags': [{'tag': tag}], 'user_id': user_id}]

@pytest.mark.notes_testing
def test_get_notes_ordered(client, auth_headers):
    response = client.get('/notes/', headers=auth_headers, params={"order_by_date":"asc"})
    assert response.status_code == 200
    assert response.json() == [
                               {'id': 1, 'text': 'testing', 'category': 'study', 'tags': [{'tag':"probando"}, {'tag':"olvidalo"}], 'user_id': 1},
                               {'id': 2, 'text': 'ojala, no', 'category': 'unknown', 'tags': [], 'user_id': 1},
                               {'id': 3, 'text': 'vvlc', 'category': 'work', 'tags': [{'tag':'cierrenlo'}], 'user_id': 1},
                               {'id': 4, 'text': "sasaki", 'category': "study", 'tags': [{'tag':'Personaje'}], 'user_id': 1}
                               ] 

    response = client.get('/notes/', headers=auth_headers, params={"order_by_date":"desc"})
    assert response.status_code == 200
    assert response.json() == [
                               {'id': 4, 'text': "sasaki", 'category': "study", 'tags': [{'tag':'Personaje'}], 'user_id': 1},
                               {'id': 3, 'text': 'vvlc', 'category': 'work', 'tags': [{'tag':'cierrenlo'}], 'user_id': 1},
                               {'id': 2, 'text': 'ojala, no', 'category': 'unknown', 'tags': [], 'user_id': 1},
                               {'id': 1, 'text': 'testing', 'category': 'study', 'tags': [{'tag':"probando"}, {'tag':"olvidalo"}], 'user_id': 1}
                               ]

@pytest.mark.notes_testing
def test_get_notes(client, auth_headers):
    response = client.get("/notes/", headers=auth_headers)
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    for user in notes:
        assert all(key in user for key in ["text","id","category", "tags", "user_id"])

@pytest.mark.notes_testing
@pytest.mark.parametrize (
    "id, expected_code, expected_detail",
    [
        (1, 202, "Nota eliminada exitosamente"),
        (10000, 404, "No se encontró la nota.")
    ] )
def test_delete_note(client, auth_headers, id, expected_code, expected_detail):
    response = client.delete("/notes/1", headers=auth_headers)
    assert response.status_code == expected_code
    assert response.json().get("detail") == expected_detail

@pytest.mark.users_testing
def test_patch_user(client, auth_headers):
    response = client.patch("/users/me", headers=auth_headers, json={"username": "testing", "password": "0000", "email":"cambio@email.com"})
    assert response.status_code == 202
    assert response.json() == {"detail":"Usuario actualizado con exito"}

# Login de usuario post update
@pytest.fixture
def auth_headers3(client):
    login_data = {"username": "alter", "password": "00000"}  # Credenciales
    response = client.post("/login", data=login_data)  # OAuth usa 'data'
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.admin_testing
def test_create_admin_user(client):
    response = client.post("/users/", json={"username": "admin", "email": "admin@email.com", "password":"admin"})
    assert response.status_code == 202
    
    session = Session(engine)
    user_found = session.get(Users, 4)
    user_found.role = 'ADMIN'
    session.commit()

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
@pytest.mark.parametrize (
    "id, username, password, email, expected_status, expected_detail",
    [
        (3, "cambiado", "1111", "cambio@email.com", 202, "El usuario fue actualizado"),
        (10000, "cambiado", "1111", "cambio@email.com", 404, "No se ha encontrado el usario")
    ]
)
def test_put_user_admin(client, auth_headers_admin, id, username, password, email, expected_status, expected_detail):
    response = client.put(f"/users/admin/{id}", headers=auth_headers_admin, json={"username": username, "password": password, "email":email})
    assert response.status_code == expected_status
    assert response.json().get("detail") == expected_detail

@pytest.mark.admin_testing
@pytest.mark.parametrize(
    "id, expected_status",
    [(2, 204),
     (10000, 404)]
)
def test_delete_user_admin(client, auth_headers_admin, id, expected_status):
    response = client.delete(f"/users/admin/{id}", headers=auth_headers_admin)
    assert response.status_code == expected_status

@pytest.fixture
def auth_headers(client):
    login_data = {"username": "test", "password": "5555"}  # Credenciales
    response = client.post("/login", data=login_data)  # OAuth usa 'data'
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.notes_testing
@pytest.mark.parametrize (
        "text, expected_status, expected_detail",
         [("ojala, no", 201, "Se creó una nueva nota."),
          ("vvlc", 201, "Se creó una nueva nota."),
          ("sasaki", 201, "Se creó una nueva nota.")
         ]
        )
def test_create_many_notes(client, auth_headers3, text, expected_status, expected_detail):
    response = client.post("/notes/", headers=auth_headers3, json={"text":text})
    assert response.status_code == expected_status
    assert response.json().get("detail") == expected_detail

@pytest.mark.admin_testing
def test_get_notes_admin(client, auth_headers_admin):
    response = client.get("/notes/admin/all/", headers=auth_headers_admin)
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    for user in notes:
        assert all(key in user for key in ["text","id","category", "tags", "user_id", "create_at"])

    response = client.get("/notes/admin/all/", headers=auth_headers_admin, params={"limit":2, "order_by_date":"asc"})
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    assert len(notes) == 2

@pytest.mark.admin_testing
def test_get_notes_admin_by_id(client, auth_headers_admin):
    response = client.get("/notes/admin/2", headers=auth_headers_admin)
    assert response.status_code == 200
    assert response.json() == {"text":"ojala, no", "user_id":1, "category":"unknown", "id":2, "tags":[]}

@pytest.mark.admin_testing
def test_failed_get_notes_admin_by_id(client, auth_headers_admin):
    response = client.get("/notes/admin/666666", headers=auth_headers_admin)
    assert response.status_code == 404
    assert response.json() == {"detail": "No se encontró la nota."}

@pytest.mark.admin_testing
@pytest.mark.parametrize(
    "id, status_expected, detail_expected",
    [(3, 202, {"detail":"Nota eliminada exitosamente"}),
     (666666, 404, {"detail":"No se encontró la nota."})]
)
def test_delete_notes_admin(client, auth_headers_admin, id, status_expected, detail_expected):
    response = client.delete(f"/notes/admin/{id}", headers=auth_headers_admin)
    assert response.status_code == status_expected
    assert response.json() == detail_expected

@pytest.mark.auth_testing
def test_user_disabled(client):
    response = client.post("/users/", json={"username":"disabled","email":"disabled@email.com","password":"disabled"})
    assert response.status_code == 202

    session = Session(engine)
    user_found = session.get(Users, 5)
    user_found.disabled = True
    session.commit()

    login_data = {"username": "disabled", "password": "disabled"}
    response = client.post("/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    header = {"Authorization": f"Bearer {token}"}

    response = client.post('/notes/', headers=header, json={'text':'inactivo'})
    response.status_code == 400
    response.json() == {'detail':'Usuario inactivo'}

@pytest.mark.auth_testing
def test_no_autenticado(client):
    response = client.get("/users/me")
    assert response.status_code == 401
    assert response.json() == {'detail' : 'Not authenticated'}

@pytest.mark.auth_testing
def test_no_autenticado(client, auth_headers3):
    response = client.get("/users/admin/2", headers=auth_headers3)
    assert response.status_code == 401
    assert response.json() == {"detail":{"UNAUTHORIZED":"No tiene autorizacion para realizar esta accion."}}

@pytest.mark.users_testing
def test_delete_actual_user(client, auth_headers3):
    response = client.delete("/users/me", headers=auth_headers3)
    assert response.status_code == 202
    assert response.json() == {"detail":"Usuario eliminado con éxito."}