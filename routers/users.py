from fastapi import APIRouter, status, HTTPException, Depends
from Models.User import User, User_BD
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
        statement = select(Users).where(Users.id == id)
        results = session.exec(statement).first()
        return results

# Crea una nueva tarea
@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def create_user(new_user : Users):
    with Session(engine) as session:
        statement = select(Users)
        results = session.exec(statement).all()
        
        for i in results:
            if i.email == new_user.email:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail={"Ya existe un usuario con este id"})

        session.add(new_user)
        session.commit()
    return {"Se creo un nuevo usuario."}

# Actualiza un usuario segun su ID
@router.put("/{id}", status_code=status.HTTP_202_ACCEPTED)
def update_user(user_: Users):
    with Session(engine) as session:
        statement = select(Users).where(Users.id == user_.id)
        user_found = session.exec(statement).first()
        user_found = user_
        session.commit()    
    return {"El usuario fue actualizado"}


# Elimina la tarea con id especifico
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id:int):
    found = False
    for index, user in enumerate(users_list):
        if user.id == id:
            del users_list[index]
            found = True
    
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"Error":"No se ha encontrado el usuario"})
    
    return {"La tarea se ha eliminado"}
    
