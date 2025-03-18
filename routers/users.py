from fastapi import APIRouter, status, HTTPException, Depends, Path, Query
from Models.db_models import Users, UserRead, UserUpdate, UserReadAdmin
from DB.database import Session, select, get_session, or_
from sqlalchemy.exc import SQLAlchemyError
from routers.auth import current_user, require_admin
import logging

# Configurar logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/users", tags=["Users"])

# Todos los usuarios disponibles
@router.get("/all-users/", status_code=status.HTTP_200_OK,
            description="Obtiene una lista de todos los usuarios, con 'limit' y 'offset' para paginar.")

def read_all_users(limit : int = Query(5, description='Indica la cantidad de resultados a recibir'),
                   offset: int = Query(0, description='Indica la cantidad que se van a saltear'),
                   username : str = Query(None, description='Indica un username para la busqueda'),
                   session : Session = Depends(get_session)) -> list[UserRead] | UserRead:
    try: 
        statement = select(Users).offset(offset).limit(limit)

        if username:
            user_found = session.exec(statement.where(Users.username == username)).first()
            if not user_found:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User no encontrado")
        else:
            user_found = session.exec(statement).all()

        return user_found
    except SQLAlchemyError as e:
        logger.error(f"Error en read_all_users: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")

# Lee el usuario actual
@router.get("/me", status_code=status.HTTP_200_OK,
            description="Obtiene los datos del usuario logeado")
def read_me(user : UserRead = Depends(current_user)) -> UserRead:
    return user

# Lee el usuario de id especifico
@router.get("/{id}", response_model=UserRead,
            status_code=status.HTTP_200_OK,
            description="Obtiene un usuario segun el id indicado")
def read_users_with_id(id: int = Path(ge=0),
                       session : Session = Depends(get_session)) -> UserRead:
    try:
        results = session.get(Users, id)

        if results is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se ha encontrado el usario")
        
        return results
    
    except Exception as e:
        logger.error(f"Error en read_users_with_id: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al obtener el usuario")

# Lee el usuario de id especifico
@router.get("/admin/{id}", response_model=UserReadAdmin, status_code=status.HTTP_200_OK,
            description="Obtiene el usuario indicado, pero muestra datos sensibles. Requiere permisos de administrador")
def read_users_with_id_for_admin(id: int = Path(ge=0), session : Session = Depends(get_session),
                                 actual_user : Users = Depends(require_admin)) -> UserReadAdmin:
    try:
        user_found = session.get(Users, id)
        if user_found is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se ha encontrado el usario")
        return user_found
    
    except Exception as e:
        logger.error(f"Error en read_users_with_id_for_admin: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al obtener el usuario")

# Crea un nuevo usuario
@router.post("/", status_code=status.HTTP_202_ACCEPTED,
             description="Crea un nuevo usuario. OBLIGATORIO: username, email y password")
def create_user(new_user : Users, session : Session = Depends(get_session)):
    
    try:
        results = session.exec(select(Users).where(or_(Users.username == new_user.username, Users.email == new_user.email))).first()
        
        if results:
            if results.username == new_user.username:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                    detail="Ya existe un usuario con este username")
            else:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                    detail="Ya existe un usuario con este email")

        # Encripta la contraseña
        new_user.password = Users.encrypt_password(new_user.password)
        
        session.add(new_user)
        session.commit()
        return {"detail" : "Se creo un nuevo usuario."}
    
    except Exception as e:
        logger.error(f"Error en create_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al crear el usuario.")

# actualiza el usuario actual
@router.patch("/me", status_code=status.HTTP_202_ACCEPTED,
              description="Actualiza el usuario actual segun el campo alterado.")
def patch_user( user_data : UserUpdate,
                session : Session = Depends(get_session),
                actual_user : Users = Depends(current_user)):
    try:
        if not actual_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se ha encontrado el usario")
        
        # Actualiza los campos del usuario
        user_data_dict = user_data.model_dump(exclude_unset=True)
        for key, value in user_data_dict.items():
            setattr(actual_user, key, value)

        # Encripta la contraseña, si es que se ha cambiado
        if user_data.password:
            actual_user.password = Users.encrypt_password(user_data.password)

        session.commit()
        return {"detail":"Usuario actualizado con exito"}

    except Exception as e:
        logger.error(f"Error en patch_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al actualizar el usuario.")

# Actualiza un usuario segun su ID
@router.put("/admin/{user_id}", status_code=status.HTTP_202_ACCEPTED,
            description="Actualiza un usuario con id especifico por completo. Requiere permisos de administrador.")
def update_user(user_id : int,
                user_data: UserUpdate,
                session : Session = Depends(get_session),
                user = Depends(require_admin)):
    try:
        statement = select(Users).where(Users.user_id == user_id)
        user_found = session.exec(statement).first()

        if not user_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se ha encontrado el usario")
        
        # Actualiza los campos del usuario
        user_data_dict = user_data.model_dump(exclude_unset=True)
        for key, value in user_data_dict.items():
            setattr(user_found, key, value)
        
        user_found.password = Users.encrypt_password(user_data.password)
        session.commit()
        return {"detail":"El usuario fue actualizado"}

    except Exception as e:
        logger.error(f"Error en update_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al actualizar el usuario.")


# Elimina el usuario actual
@router.delete("/me", status_code=status.HTTP_202_ACCEPTED,
               description="Elimina el usuario actual. Tambien se eliminan las tareas relacionadas al usuario.")
def delete_actual_user(actual_user = Depends(current_user), session : Session = Depends(get_session)):
    try:
        session.delete(actual_user)
        session.commit()
        return {"detail":"Usuario eliminado con éxito."}

    except Exception as e:
        logger.error(f"Error en delete_actual_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar el usuario")

# Elimina el usuario indicado por id
@router.delete("/admin/{id_}", status_code=status.HTTP_204_NO_CONTENT,
               description="Elimina el usuario de id especifico. Requiere permisos de administrador.")
def delete_actual_user(id_ : int,
                       user = Depends(require_admin),
                       session : Session = Depends(get_session)):
    try:
        resultado = session.get(Users, id_)
        
        if not resultado:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se ha encontrado el usario")
        
        session.delete(resultado)
        session.commit()
        return status.HTTP_204_NO_CONTENT
    
    except Exception as e:
        logger.error(f"Error en delete_actual_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar el usuario")