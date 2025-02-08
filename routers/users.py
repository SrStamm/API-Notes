from fastapi import APIRouter, status, HTTPException, Depends
from Models.db_models import Users, UserRead
from DB.database import Session, engine, select
from routers.auth import encrypt_password, current_user

# Router
router = APIRouter(prefix="/users", tags=["Users"])

# Lee el usuario actual
@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
def read_me(user : UserRead = Depends(current_user)):
    return user

# Lee todos los usuarios
@router.get("/", status_code=status.HTTP_200_OK)
def get_users_all(user = Depends(current_user)):
    if user.permission is True:
        with Session(engine) as session:
            statement = select(Users)
            user_found = session.exec(statement).all()
        return user_found
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail={"error":"No estas autorizado para ejecutar esta accion"})


# Lee el usuario de id especifico
@router.get("/{id}", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_users_with_id(id: int):
    with Session(engine) as session:
        statement = select(Users).where(Users.user_id == id)
        results = session.exec(statement).first()

        # Comprueba si es nulo, y lanza una excepcion si es asi
        if results is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
        else:
            return results

# Crea un nuevo usuario
@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def create_user(new_user : Users):
    with Session(engine) as session:
        statement = select(Users).where(Users.username == new_user.username)
        results = session.exec(statement).first()
        
        if results is not None:
            statement = select(Users).where(Users.email == new_user.email)
            results = session.exec(statement).first()

            if results is not None:
                session.add(new_user)
                session.commit()
                session.refresh(new_user)
                new_user.password = encrypt_password(new_user.password)
                session.commit()
                return {"Se creo un nuevo usuario."}
            else:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                     detail={"error" : "Ya existe un usuario con este email"})
        else:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                     detail={"error" : "Ya existe un usuario con este username"})

# Actualiza un usuario segun su ID
@router.put("/{user_id}", status_code=status.HTTP_202_ACCEPTED)
def update_user(user_id : int, user: Users):
    with Session(engine) as session:
        statement = select(Users).where(Users.user_id == user_id)
        user_found = session.exec(statement).first()

        # Comprueba si es nulo, y lanza una excepcion si es asi
        if user_found is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
        else:
            if user.email is not None:
                user_found.email = user.email
            if user.password is not None:
                user_found.password = encrypt_password(user.password)
            if user.username is not None:
                user_found.username = user.username
            if user.permission is not None:
                user_found.username = user.permission
            session.commit()    
        return {"El usuario fue actualizado"}


# Elimina el usuario actual
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_actual_user(user = Depends(current_user)):
    with Session(engine) as session:
        statement = select(Users).where(Users.user_id == user.user_id)
        me = session.exec(statement).first()
        session.delete(me)
        session.commit()
        return {"detail" : "El usuario se ha eliminado con éxito"}
        

# Elimina el usuario indicado por id
@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete_actual_user(id_ : int, user = Depends(current_user)):
    if user.permission is True:
        with Session(engine) as session:
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