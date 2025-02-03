from fastapi import APIRouter, status, HTTPException
from Models.db_models import Tasks, TaskRead
from DB.database import Session, engine, select

# Router de la app
router = APIRouter(prefix="/tasks", tags=["Tasks"])

# Lee todas las tareas
@router.get("/")
def tasks_all():
    with Session(engine) as session:
        statement = select(Tasks)
        results = session.exec(statement).all()
        return results


# Lee la tarea de id especifico
@router.get("/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=TaskRead)
def tasks_search_id(id: int):
    with Session(engine) as session:
        statement = select(Tasks).where(Tasks.id == id)
        results = session.exec(statement).first()
        return results
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"No se encontro la nota"})


# Crea una nueva tarea
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(task : Tasks):
    with Session(engine) as session:
        session.add(task)
        session.commit()
        return {"Se creo una nueva tarea."}


# Actualiza un usuario segun su ID
@router.put("/{id}", status_code=status.HTTP_202_ACCEPTED)
def update_task(task: Tasks):
    with Session(engine) as session:
        statement = select(Tasks).where(Tasks.id == task.id)
        result = session.exec(statement)
    
        task_selected = result.one()        # Obtiene un unico valor
        
        if task_selected is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error":"No se ha encontrado la nota"})
        else:
            task_selected.text = task.text      # Se modifica el registro
            session.commit()                    # Se guardan los cambios
            return {"detail" : "Ha sido actualizado con exito"}


# Elimina la tarea con id especifico
@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id_ : int):
    with Session(engine) as session:
        statement = select(Tasks).where(Tasks.id == id_)
        results = session.exec(statement).first()

        if results is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error":"No se ha encontrado la nota"})
        else:
            session.delete(results)
            session.commit()
            return {"Se ha eliminado exitosamente"}