from fastapi import APIRouter, status, HTTPException, Depends, Path, Query
from Models.db_models import Users, UserRead, UserUpdate
from DB.database import Session, engine, select, get_session
from routers.auth import encrypt_password, current_user

# Router
router = APIRouter(prefix="/users", tags=["Users"])

# Todos los usuarios disponibles
@router.get("/", status_code=status.HTTP_200_OK,
            description="Obtiene una lista de todos los usuarios, con limite de cantidad a mostrar")
def read_all_users(limit : int = 5,
                   offset: int = 0,
                   session : Session = Depends(get_session)) -> list[UserRead]:

    statement = select(Users).offset(offset).limit(limit)
    user_found = session.exec(statement).all()
    return user_found

# Lee el usuario actual
@router.get("/me", status_code=status.HTTP_200_OK,
            description="Obtiene los datos del usuario actual")
def read_me(user : UserRead = Depends(current_user)) -> UserRead:
    return user

# Lee el usuario de id especifico
@router.get("/{id}", response_model=UserRead, status_code=status.HTTP_200_OK,
            description="Obtiene un usuario segun el id indicado")
def read_users_with_id(id: int = Path(ge=0), session : Session = Depends(get_session)) -> UserRead:
    statement = select(Users).where(Users.user_id == id)
    results = session.exec(statement).first()

    if results is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
    else:
        return results

# Lee el usuario de id especifico
@router.get("/{id}/admin", response_model=UserRead, status_code=status.HTTP_200_OK,
            description="Obtiene el usuario indicado, pero muestra datos sensibles")
def read_users_with_id_for_admin(id: int = Path(ge=0), session : Session = Depends(get_session),
                                 actual_user : Users = Depends(current_user)) -> Users:
    if actual_user.permission is False:
        HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error":"No estas autorizado"})

    statement = select(Users).where(Users.user_id == id)
    user_found = session.exec(statement).first()

    if user_found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
    return user_found

# Crea un nuevo usuario
@router.post("/", status_code=status.HTTP_202_ACCEPTED,
             description="Crea un nuevo usuario")
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
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    new_user.password = encrypt_password(new_user.password)
    session.commit()
    return {"detail" : "Se creo un nuevo usuario."}

# actualiza el usuario actual
@router.patch("/me", status_code=status.HTTP_202_ACCEPTED)
def patch_user(user_data : UserUpdate,
                session : Session = Depends(get_session),
                actual_user : Users = Depends(current_user)):
    try:
        statement = select(Users).where(Users.user_id == actual_user.user_id)
        user_found = session.exec(statement).first()

        if user_found is None:
            HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
        
        if user_data.username is not None:
            user_found.username = user_data.username

        if user_data.email is not None:
            user_found.email = user_data.email
        
        if user_data.password is not None:
            user_found.password = user_data.password
        
        if user_data.permission is not None:
            user_found.permission = user_data.permission

        session.commit()
        return {"detail":"Usuario actualizado con exito"}

    except:
        HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al actualizar el usuario.")

# Actualiza un usuario segun su ID
@router.put("/{user_id}", status_code=status.HTTP_202_ACCEPTED)
def update_user(user_id : int, user_data: UserUpdate, session : Session = Depends(get_session)):
    try:
        statement = select(Users).where(Users.user_id == user_id)
        user_found = session.exec(statement).first()

        # Comprueba si es nulo, y lanza una excepcion si es asi
        if user_found is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
        
        if user_data.email is not None:
            user_found.email = user_data.email
        if user_data.password is not None:
            user_found.password = encrypt_password(user_data.password)
        if user_data.username is not None:
            user_found.username = user_data.username
        if user_data.permission is not None:
            user_found.permission = user_data.permission
        session.commit()
        return {"detail":"El usuario fue actualizado"}

    except:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al actualizar el usuario.")


# Elimina el usuario actual
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_actual_user(actual_user = Depends(current_user), session : Session = Depends(get_session)):
    try:
        session.delete(actual_user)
        session.commit()
        return {"detail" : "El usuario se ha eliminado con éxito"}

    except:
        HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar el usuario")

# Elimina el usuario indicado por id
@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete_actual_user(id_ : int, user = Depends(current_user), session : Session = Depends(get_session)):
    if user.permission is True:
        statement = select(Users).where(Users.user_id == id_)
        resultado = session.exec(statement).first()

        if resultado is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
        
        session.delete(resultado)
        session.commit()
        return {"detail" : "El usuario se ha eliminado con éxito"}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"error":"No estas autorizado para ejecutar esta accion"})