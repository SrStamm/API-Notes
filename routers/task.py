from fastapi import APIRouter, status, HTTPException, Depends
from Models.db_models import Tasks, TaskRead
from DB.database import Session, engine, select
from routers.auth import current_user

# Router de la app
router = APIRouter(prefix="/tasks", tags=["Tasks"])


# Lee todas las tareas del usuario actual
@router.get("/")
def get_tasks_user(user = Depends(current_user)):
    
    with Session(engine) as session:
        statement = select(Tasks).where(Tasks.user_id == user.user_id)
        results = session.exec(statement).all()
        return results


# Lee todas las tareas
@router.get("/all")
def get_tasks_all(user = Depends(current_user)):
    if user.permission is True:
        with Session(engine) as session:
            statement = select(Tasks)
            results = session.exec(statement).all()
            return results
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail={"error":"No estas autorizado para ejecutar esta accion"})

# Lee la tarea de id especifico
@router.get("/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=TaskRead)
def tasks_search_id(id: int, user = Depends(current_user)):
    with Session(engine) as session:
        statement = select(Tasks).where(Tasks.id == id, Tasks.user_id == user.user_id)
        results = session.exec(statement).first()
        
        if results is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"No se encontro la nota"})
        else:
            return results
    

# Crea una nueva tarea
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(task: Tasks, user=Depends(current_user)):
    with Session(engine) as session:
        # Inserta el user_id del usuario autenticado
        task.user_id = user.user_id 

        session.add(task)
        session.commit()
        session.refresh(task)
    return {"detail": "Se creó una nueva tarea."}


# Actualiza un usuario segun su ID
@router.put("/{id}", status_code=status.HTTP_202_ACCEPTED)
def update_task(task: Tasks, user=Depends(current_user)):
    with Session(engine) as session:
        statement = select(Tasks).where(Tasks.id == task.id, Tasks.user_id == user.user_id)
        result = session.exec(statement)
    
        task_selected = result.one()        # Obtiene un unico valor
        
        if task_selected is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error":"No se ha encontrado la nota"})
        else:
            task_selected.text = task.text      # Se modifica el registro
            task_selected.title = task.title
            task_selected.category = task.category
            session.commit()                    # Se guardan los cambios
            return {"detail" : "Ha sido actualizado con exito"}


# Elimina la tarea con id especifico
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id : int, user = Depends(current_user)):
    with Session(engine) as session:
        statement = select(Tasks).where(Tasks.id == id, Tasks.user_id == user.user_id)
        results = session.exec(statement).first()

        if results is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error":"No se ha encontrado la nota"})
        else:
            session.delete(results)
            session.commit()
            return {"Se ha eliminado exitosamente"}