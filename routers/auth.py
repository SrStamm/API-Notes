from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from Models.db_models import Users, Sessions
from DB.database import Session, select, get_session
from uuid import uuid4

router = APIRouter(prefix="/login", tags=["Authentication"])

# Definimos el algoritmo
ALGORITHM = "HS256"

# Duracion de los tokens
ACCESS_TOKEN_DURATION = 15
REFRESH_TOKEN_DURATION = 7

# Definimos una llave secreta
SECRET = "MW6mdMOU8Ga58KSty8BYakM185zW857fZlTBqdmp1JkVih3qqr"

# Contexto de encriptacion 
crypt = CryptContext(schemes=["bcrypt"])

# Se declara la url donde se obtiene el token
oauth2 = OAuth2PasswordBearer(tokenUrl="login", scheme_name="Bearer")


@router.post("/")
async def login(form: OAuth2PasswordRequestForm = Depends(),
                session : Session = Depends(get_session)):
    # Busqueda del usuario
    statement = select(Users).where(Users.username == form.username)
    user_found = session.exec(statement).first()

    if user_found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuario no encontrado o no existe")
    
    # Caso no tenga el mismo password, da error
    if not crypt.verify(form.password, user_found.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña incorrecta")

    # Generar los tokens
    jti = str(uuid4())
    refresh_token = str(uuid4())

    # Declarar la fecha de expiracion
    access_expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_DURATION)
    refresh_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DURATION)

    access_token = {
        "sub": str(user_found.user_id),
        "exp": access_expires.timestamp(),
        "jti": jti
}
    
    encoded_access_token = jwt.encode(access_token, SECRET, algorithm=ALGORITHM)

    # Crear sesión en DB
    db_session = Sessions(
        session_id=jti,
        user_id=user_found.user_id,
        access_token= encoded_access_token,
        refresh_token=refresh_token,
        access_expires=access_expires,
        refresh_expires= refresh_expires
    )

    session.add(db_session)
    session.commit()

    # Devuelve el token de acceso
    return {"access_token" : encoded_access_token,
            "refresh_token": refresh_token,
            "token_type" : "bearer"}


@router.post("/refresh")
async def refresh_token(refresh_token: str,
                session : Session = Depends(get_session)):
    
    # Busqueda del token
    result = session.exec(
        select(Sessions)
        .where(Sessions.refresh_token == refresh_token)
        .where(Sessions.is_active == True)
        ).first()
    
    # Comprobacion del resultado
    if not result or result.refresh_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid Refresh Token")

    # Invalidar la session actual
    result.is_active = False
    session.commit()

    # Nuevo token
    new_jti = str(uuid4())
    new_refresh_token = str(uuid4())

    new_access_token = {
        "sub": str(result.user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_DURATION),
        "jti": new_jti
    }

    encoded_access_token = jwt.encode(new_access_token, SECRET, algorithm=ALGORITHM)

    # Crear nueva sesion
    new_session = Sessions(
        session_id= new_jti,
        user_id= result.user_id,
        access_token= jwt.encode(new_access_token, SECRET, algorithm=ALGORITHM),
        refresh_token= new_refresh_token,
        access_expires= new_access_token["exp"],
        refresh_expires= datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DURATION)
    )

    session.add(new_session)
    session.commit()

    return {
        "access_token": encoded_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


# Funcion que encripta la contraseña
def encrypt_password(password : str):
    password = password.encode()
    return crypt.hash(password)

# Proceso de validacion de Token encriptado
async def auth_user(token: str = Depends(oauth2), session : Session = Depends(get_session)):

    try:
        # Decodifica el jwt
        payload = jwt.decode(token, SECRET, algorithms=ALGORITHM)
        # Obtiene los datos necesarios
        user_id = payload.get("sub")
        jti = payload.get("jti")
        
        if not user_id or not jti:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        # Verificar en base de datos
        db_session = session.exec(
            select(Sessions)
            .where(Sessions.session_id == jti)
            .where(Sessions.is_active == True)
            .where(Sessions.access_expires > datetime.now(timezone.utc))
        ).first()
        
        user = session.get(Users, db_session.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        return user
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Valida si el user esta acivo
async def current_user(user: Users = Depends(auth_user)):
    if user.disabled is True:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Usuario inactivo")
    return user

async def require_admin(user : Users = Depends(current_user)):
    if user.role == 'admin':
        return user
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"UNAUTHORIZED":"No tiene autorizacion para realizar esta accion."})    