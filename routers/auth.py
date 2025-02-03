from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from Models.User import User, User_BD
from Models.db_models import Users

router = APIRouter(tags=["Authentication"])

# Definimos el algoritmo
ALGORITHM = "HS256"

# Definimos la duracion del TOKEN
ACCESS_TOKEN_DURATION = 1

# Definimos una llave secreta
SECRET = "MW6mdMOU8Ga58KSty8BYakM185zW857fZlTBqdmp1JkVih3qqr"

# Contexto de encriptacion 
crypt = CryptContext(schemes=["bcrypt"])

# Se declara la url donde se obtiene el token
oauth2 = OAuth2PasswordBearer(tokenUrl="login")

def encrypt_password(password : str):
    return crypt.encrypt(password)

# Lista de usuarios
users_db = {
    "mirko_dev" : {"id":1, "username":"mirko_dev", "email":"mirko@dev.com", "disabled": False, "password":"$2a$12$3X0URv8RM5NvN4pdw58QlO.77VDfbSXRTzTMY98T6U4oLFYSD3AjW"},
    "moure_dev" : {"id":2, "username":"moure_dev", "email":"moure@dev.com", "disabled": True, "password":"$2a$12$xlWIfXHnxGy87Mr1oNH2r.vYr6K.3JDXpqSXz9RjVQfU4ZQ6Gj5Bm"}
}

# Funcion de busqueda por username
def search_user_db(username:str):
    if username in users_db:
        return User_BD(**users_db[username])

# funcion que busca el usuario
def search_user(username: str):
    if username in users_db:
        return User(**users_db[username])

# Proceso de validacion de Token encriptado
async def auth_user(token: str = Depends(oauth2)):
    
    exception = HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Credenciales de autenticación inválidas", 
                    headers={"WWW-Authenticate": "Bearer"})
    
    # Desencriptando el token
    try:
        username = jwt.decode(token, SECRET, algorithms=ALGORITHM).get("sub")
        if username is None:
            raise  exception

    except JWTError: 
        raise exception 

    return search_user(username)


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):

    # Obtiene el usuario con el mismo username
    user_list = users_db.get(form.username)

    # Si no esta en la lista, da error
    if not user_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario no es correcto")

    # Busca el usuario 
    user = search_user_db(form.username)

    # Caso no tenga el mismo password, da error
    if not crypt.verify(form.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La contraseña no es correcta")
    
    # Caso el usuario este desactivado
    if user.disabled is True:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="El usuario esta desactivado")
    
    access_token = {"sub": user.username,
                    "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_DURATION)}

    # Devuelve el token de acceso
    return {"access_token" : jwt.encode(access_token, SECRET, algorithm=ALGORITHM), "token_type" : "bearer"}

# Lee los datos del usuario
@router.get("/login/me")
async def me(user: User = Depends(auth_user)):
    return user