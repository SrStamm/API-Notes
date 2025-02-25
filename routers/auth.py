from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from Models.db_models import Users
from DB.database import Session, engine, select

router = APIRouter(prefix="/login", tags=["Authentication"])

# Definimos el algoritmo
ALGORITHM = "HS256"

# Definimos la duracion del TOKEN
ACCESS_TOKEN_DURATION = 30

# Definimos una llave secreta
SECRET = "MW6mdMOU8Ga58KSty8BYakM185zW857fZlTBqdmp1JkVih3qqr"

# Contexto de encriptacion 
crypt = CryptContext(schemes=["bcrypt"])

# Se declara la url donde se obtiene el token
oauth2 = OAuth2PasswordBearer(tokenUrl="login")

# Funcion que encripta la contraseña
def encrypt_password(password : str):
    password = password.encode()
    return crypt.hash(password)

# Proceso de validacion de Token encriptado
async def auth_user(token: str = Depends(oauth2)):
    # authorization: str = Header(oauth2, description="Token de Acceso Bearer")
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

    with Session(engine) as session:
        statement = select(Users).where(Users.username == username)
        user_found = session.exec(statement).first()
        return user_found


@router.post("/")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        statement = select(Users).where(Users.username == form.username)
        user_found = session.exec(statement).first()

        if user_found is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Usuario no encontrado o no existe")

        # Caso no tenga el mismo password, da error
        if not crypt.verify(form.password, user_found.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña incorrecta")

        if user_found.disabled is True:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Usuario inactivo")
    
        access_token = {"sub": user_found.username,
                        "exp": datetime.now() + timedelta(minutes=ACCESS_TOKEN_DURATION)}

        # Devuelve el token de acceso
        return {"access_token" : jwt.encode(access_token, SECRET, algorithm=ALGORITHM), "token_type" : "bearer"}

# Valida si el user esta acivo
async def current_user(user: Users = Depends(auth_user)):
    if user.disabled == True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Usuario inactivo")
      
    return user