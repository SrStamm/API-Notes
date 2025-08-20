from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from Models.db_models import Users, Sessions, read_session
from DB.database import Session, select, get_session
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])

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


# Funcion que encripta la contraseña
def encrypt_password(password : str):
    password_encoded = password.encode()
    return crypt.hash(password_encoded)

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

        if not db_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no autenticado")

        user = session.exec(select(Users).where(Users.user_id == db_session.user_id)).first()

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


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(),
                session : Session = Depends(get_session)):

    try:
        statement = select(Users.user_id, Users.username, Users.password).where(Users.username == form.username)
        user_found = session.exec(statement).first()

        if not user_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Usuario no encontrado o no existe")

        if not crypt.verify(form.password, user_found.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña incorrecta")

        jti = str(uuid4())
        refresh_token = str(uuid4())

        access_expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_DURATION)
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DURATION)

        access_token = {
            "sub": str(user_found.user_id),
            "exp": access_expires.timestamp(),
            "jti": jti
        }

        encoded_access_token = jwt.encode(access_token, SECRET, algorithm=ALGORITHM)

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

        return {"access_token" : encoded_access_token,
                "refresh_token": refresh_token,
                "token_type" : "bearer"}

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en delete_note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar la nota.")


@router.post("/logout")
def cerrar_sesion(session: Session = Depends(get_session),
                  user: Users = Depends(current_user),
                  token: str = Depends(oauth2)):

    try:
        payload = jwt.decode(token, SECRET, algorithms=ALGORITHM)
        jti = payload.get("jti")
        session_found = session.exec(
                            select(Sessions)
                            .where(Sessions.user_id == user.user_id)
                            .where(Sessions.session_id == jti))

        if not session_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

        session_found.is_active = False
        session.commit()

        return {"detail":"Sesion terminada"}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en delete_note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar la nota.")

@router.post("/refresh")
async def refresh_token(refresh_token: str,
                        session : Session = Depends(get_session)):

    # Busqueda del token
    result = session.exec(
        select(Sessions.refresh_token, Sessions.refresh_expires, Sessions.is_active)
        .where(Sessions.refresh_token == refresh_token)
        .where(Sessions.is_active == True)
        ).first()
    try: 
        # Comprobacion del resultado
        if not result or result.refresh_expires < datetime.now():
            raise HTTPException(status_code=401, detail="Invalid Refresh Token")

        # Invalidar la session actual
        result.is_active = False
        session.commit()

        # Nuevo token
        new_jti = str(uuid4())
        new_refresh_token = str(uuid4())

        nex_access_expires = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_DURATION)
        nex_refresh_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DURATION)

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
            access_token= encoded_access_token,
            refresh_token= new_refresh_token,
            access_expires= nex_access_expires,
            refresh_expires= nex_refresh_expires
        )

        session.add(new_session)
        session.commit()

        return {
            "access_token": encoded_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en refresh_token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al actualizar el token.")

@router.get("/sessions")
def get_user_sessions(session: Session = Depends(get_session),
                  user: Users = Depends(current_user)) -> list[read_session]:

    try:
        all_sessions = session.exec(select(Sessions)
                                    .join(Users, Sessions.user_id == Users.user_id)
                                    .where(Sessions.user_id == user.user_id)
                                    ).all()

        return all_sessions

    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No se encontraran las sesiones')

@router.delete("/sessions/all-sessions", status_code=status.HTTP_202_ACCEPTED, description="Permite desactivar todas las sesiones del usuario autenticado")
def deactivate_all_session(session: Session = Depends(get_session),
                       user: Users = Depends(current_user)):

    try:
        all_session_found = session.exec(select(Sessions)
                                    .join(Users, Sessions.user_id == Users.user_id)
                                    .where(Sessions.user_id == user.user_id)).all()

        if not all_session_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesion no encontrada")

        for one_session in all_session_found:
            one_session.is_active = False

        session.commit()

        return {"detail":"Sesión desactivada con exito"}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en delete_note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar la nota.")

@router.delete("/sessions/{session_id}", status_code=status.HTTP_202_ACCEPTED, description="Permite desactivar una sesion del usuario autenticado")
def deactivate_session(session: Session = Depends(get_session),
                       user: Users = Depends(current_user),
                       session_id : str = str):

    try:
        session_found = session.exec(select(Sessions)
                                    .join(Users, Sessions.user_id == Users.user_id)
                                    .where(Sessions.user_id == user.user_id)
                                    .where(Sessions.session_id == session_id)).first()

        if not session_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesion no encontrada")

        session_found.is_active = False
        session.commit()

        return {"detail":"Sesión desactivada con exito"}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en delete_note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar la nota.")
