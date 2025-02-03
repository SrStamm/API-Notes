from fastapi import APIRouter, status, HTTPException
from Models.db_models import Users
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from DB.database import Session, engine, select

# Router
router = APIRouter(prefix="/users", tags=["Users"])

oauth2 = OAuth2PasswordBearer(tokenUrl="login")


# Lee todas las tareas
@router.get("/")
def get_users_all():
    with Session(engine) as session:
        statement = select(Users)
        results = session.exec(statement).all()
        return results

# Lee la tarea de id especifico
@router.get("/{id}")
def get_users_with_id(id: int):
    with Session(engine) as session:
        statement = select(Users).where(Users.user_id == id)
        results = session.exec(statement).first()

        if results is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
        else:
            return results

# Crea una nueva tarea
@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def create_user(new_user : Users):
    with Session(engine) as session:
        statement = select(Users)
        results = session.exec(statement).all()
        
        for i in results:
            if i.email == new_user.email:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                     detail={"error" : "Ya existe un usuario con este email"})
        else:
            session.add(new_user)
            session.commit()
            return {"Se creo un nuevo usuario."}

# Actualiza un usuario segun su ID
@router.put("/{user_id}", status_code=status.HTTP_202_ACCEPTED)
def update_user(user: Users):
    with Session(engine) as session:
        statement = select(Users).where(Users.user_id == user.user_id)
        user_found = session.exec(statement).first()

        if user_found is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No se ha encontrado el usario"})
        else:
            user_found.email = user.email
            user_found.password = user.password
            user_found.username = user.username
            session.commit()    
        return {"El usuario fue actualizado"}


# Elimina la tarea con id especifico
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