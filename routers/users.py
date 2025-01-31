from fastapi import APIRouter, status, HTTPException, Depends
from Models.User import User, User_BD
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter(prefix="/users", tags=["Users"])

oauth2 = OAuth2PasswordBearer(tokenUrl="login")

# Lista de usuarios
users_list = [
    User_BD(id=1, username="Mirko", email="mirko@dev.com", disabled=False, password="123456"),
    User_BD(id=2, username="Moure", email="moure@dev.com", disabled=False, password="159753"),
    User_BD(id=3, username="Dalto", email="dalto@dev.com", disabled=False, password="123789")
]


# Lista de usuarios
users_db = {
    "mirko_dev" : {"id":1, "username":"mirko_dev", "email":"mirko@dev.com", "disabled": False, "password":"$2a$12$3X0URv8RM5NvN4pdw58QlO.77VDfbSXRTzTMY98T6U4oLFYSD3AjW"},
    "moure_dev" : {"id":2, "username":"moure_dev", "email":"moure@dev.com", "disabled": True, "password":"$2a$12$xlWIfXHnxGy87Mr1oNH2r.vYr6K.3JDXpqSXz9RjVQfU4ZQ6Gj5Bm"}
}

# Lee todas las tareas
@router.get("/")
def get_users_all():
    return users_list

# Lee la tarea de id especifico
@router.get("/{id}")
def get_users_with_id(id: int):
    return search_user_by_id(id)

# Crea una nueva tarea
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(user : User):
    # Verificamos que no exista una tarea con el mismo id
    for index, user_search in enumerate(users_list):
        if user_search.id == user.id:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail={"Ya existe un usuario con este id"})
    
    users_list.append(user)
    return {"Se creo un nuevo usuario."}

# Actualiza un usuario segun su ID
@router.put("/{id}", status_code=status.HTTP_202_ACCEPTED)
def update_task(user: User):
    found = False   # Indica si se encontro el usuario

    for index, user_search in enumerate(users_list):
        if user_search.id == user.id:
            users_list[index] = user
            found = True
    
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"No se ha encontrado el usuario"})
    else: 
        return {"El usuario fue actualizado"}


# Elimina la tarea con id especifico
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id:int):
    found = False
    for index, user in enumerate(users_list):
        if user.id == id:
            del users_list[index]
            found = True
    
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"Error":"No se ha encontrado el usuario"})
    
    return {"La tarea se ha eliminado"}

# Funcion de busqueda por id
def search_user_by_id(id: int):
    user_searched = filter(lambda user: user.id == id, users_list)
    try:    
        return list(user_searched)[0]
    except:
        return {"error":"No se ha encontrado el usuario"}
    
# Funcion de busqueda por username
def search_user_by_username(username:str):
    if username in users_list:
        return User(users_list[username])
    
