from fastapi import APIRouter, status, HTTPException, Depends, Path
from Models.db_models import Users, UserRead, UserUpdate, UserReadAdmin
from DB.database import Session, select, get_session
from routers.auth import encrypt_password, current_user, require_admin

# Router
router = APIRouter(prefix="/users", tags=["Users"])

# Todos los usuarios disponibles
@router.get("/all-users/", status_code=status.HTTP_200_OK,
            description="Obtiene una lista de todos los usuarios, con 'limit' y 'offset' para paginar.")

def read_all_users(limit : int = 5,
                   offset: int = 0,
                   username : str | None = None,
                   session : Session = Depends(get_session)) -> list[UserRead]:

    statement = select(Users).offset(offset).limit(limit)
    
    if username is not None:
        statement.where(Users.username == username)

    user_found = session.exec(statement).all()
    
    return user_found

# Lee el usuario actual
@router.get("/me", status_code=status.HTTP_200_OK,
            description="Obtiene los datos del usuario logeado")
def read_me(user : UserRead = Depends(current_user)) -> UserRead:
    return user

# Lee el usuario de id especifico
@router.get("/{id}", response_model=UserRead, status_code=status.HTTP_200_OK,
            description="Obtiene un usuario segun el id indicado")
def read_users_with_id(id: int = Path(ge=0),
                       session : Session = Depends(get_session)) -> UserRead:
    results = session.get(Users, id)

    if results is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
    
    return results

# Lee el usuario de id especifico
@router.get("/{id}/admin", response_model=UserReadAdmin, status_code=status.HTTP_200_OK,
            description="Obtiene el usuario indicado, pero muestra datos sensibles. Requiere permisos de administrador")
def read_users_with_id_for_admin(id: int = Path(ge=0), session : Session = Depends(get_session),
                                 actual_user : Users = Depends(require_admin)) -> UserReadAdmin:
    user_found = session.get(Users, id)

    if user_found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
    return user_found

# Crea un nuevo usuario
@router.post("/", status_code=status.HTTP_202_ACCEPTED,
             description="Crea un nuevo usuario. Necesita un username, email y password")
def create_user(new_user : Users, session : Session = Depends(get_session)):

    statement = select(Users).where(Users.username == new_user.username)
    results = session.exec(statement).first()
    
    if results is not None:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                    detail={"error" : "Ya existe un usuario con este username"})
    
    statement = select(Users).where(Users.email == new_user.email)
    results = session.exec(statement).first()

    if results is not None:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                detail={"error" : "Ya existe un usuario con este email"})

    new_user.password = encrypt_password(new_user.password)    
    session.add(new_user)
    session.commit()
    return {"detail" : "Se creo un nuevo usuario."}

# actualiza el usuario actual
@router.patch("/me", status_code=status.HTTP_202_ACCEPTED,
              description="Actualiza el usuario actual segun el campo alterado.")
def patch_user(user_data : UserUpdate,
                session : Session = Depends(get_session),
                actual_user : Users = Depends(current_user)):
    try:
        # statement = select(Users).where(Users.user_id == actual_user.user_id)
        user_found = session.get(Users, actual_user.user_id)

        if not user_found:
            HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
        
        user_data_dict = user_data.model_dump(exclude_unset=True)
        for key, value in user_data_dict.items():
            setattr(user_found, key, value)

        session.commit()
        return {"detail":"Usuario actualizado con exito"}

    except:
        HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al actualizar el usuario.")

# Actualiza un usuario segun su ID
@router.put("/{user_id}", status_code=status.HTTP_202_ACCEPTED,
            description="Actualiza un usuario con id especifico. Requiere permisos de administrador.")
def update_user(user_id : int,
                user_data: UserUpdate,
                session : Session = Depends(get_session),
                user = Depends(require_admin)):
    try:
        statement = select(Users).where(Users.user_id == user_id)
        user_found = session.exec(statement).first()

        # Comprueba si es nulo, y lanza una excepcion si es asi
        if user_found is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
        
        user_data_dict = user_data.dict()
        for key, value in user_data_dict.items():
            setattr(user_found, key, value)
        
        user_found.password = encrypt_password(user_data.password)
        session.commit()
        return {"detail":"El usuario fue actualizado"}

    except:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al actualizar el usuario.")


# Elimina el usuario actual
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT,
               description="Elimina el usuario actual. Tambien se eliminan las tareas relacionadas al usuario.")
def delete_actual_user(actual_user = Depends(current_user), session : Session = Depends(get_session)):
    try:
        session.delete(actual_user)
        session.commit()
        return {"detail" : "El usuario se ha eliminado con éxito"}

    except:
        HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar el usuario")

# Elimina el usuario indicado por id
@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT,
               description="Elimina el usuario de id especifico. Requiere permisos de administrador.")
def delete_actual_user(id_ : int, user = Depends(require_admin), session : Session = Depends(get_session)):
    resultado = session.get(Users, id_)
    
    if resultado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
    
    session.delete(resultado)
    session.commit()
    return {"detail" : "El usuario se ha eliminado con éxito"}