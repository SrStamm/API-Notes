from fastapi import APIRouter, status, HTTPException
from Models.Task import Task
from Models.db_models import Tasks
from DB.database import Session, engine, select

# Base.metadata.create_all(bind=engine)

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
@router.get("/{id}", status_code=status.HTTP_202_ACCEPTED)
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
        
        # Obtiene un unico valor
        task_selected = result.one()
        
        # Se modifica el registro
        task_selected.text = task.text
        
        # Se guardan los cambios
        session.commit()
        
        return {"Ha sido actualizado con exito"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"No se pudo actualizar la nota"})





# Elimina la tarea con id especifico
@router.delete("/d/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id_ : int):
    busqueda = Tasks(id=id_, text=".")
    with Session(engine) as session:
        statement = select(Tasks).where(Tasks.id == busqueda.id)
        results = session.exec(statement).first()
        print(busqueda)
        return busqueda