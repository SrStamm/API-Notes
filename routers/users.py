from fastapi import APIRouter, status, HTTPException
from Models.db_models import Users, UserRead
from DB.database import Session, engine, select
from routers.auth import encrypt_password

# Router
router = APIRouter(prefix="/users", tags=["Users"])

# Lee todos los usuarios
@router.get("/", status_code=status.HTTP_200_OK, response_model=UserRead)
def get_users_all():
    with Session(engine) as session:
        statement = select(Users)
        user_found = session.exec(statement).all()
    return user_found

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
        statement = select(Users)
        results = session.exec(statement).all()
        
        # Comprueba si ya existe ese email, y lanza una excepcion si es asi
        for i in results:
            if i.email == new_user.email:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                     detail={"error" : "Ya existe un usuario con este email"})
        else:
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            new_user.password = encrypt_password(new_user.password)
            session.commit()
            return {"Se creo un nuevo usuario."}

# Actualiza un usuario segun su ID
@router.put("/{user_id}", status_code=status.HTTP_202_ACCEPTED)
def update_user(user_id : int, user: Users):
    with Session(engine) as session:
        statement = select(Users).where(Users.user_id == user_id)
        user_found = session.exec(statement).first()

        # Comprueba si es nulo, y lanza una excepcion si es asi
        if user_found is None:
            print(user_found)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
        else:
            if user.email is not None:
                user_found.email = user.email
            if user.password is not None:
                user_found.password = encrypt_password(user.password)
            if user.username is not None:
                user_found.username = user.username
            session.commit()    
        return {"El usuario fue actualizado"}


# Elimina el usuario con id especifico
@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id_ : int):
    with Session(engine) as session:
        statement = select(Users).where(Users.user_id == id_)
        resultado = session.exec(statement).first()

        if resultado is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
        else:
            session.delete(resultado)
            session.commit()
        
        return {"detail" : "El usuario se ha eliminado con éxito"}