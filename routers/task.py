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
@router.get("/{id}")
def tasks_search_id(id: int):
    with Session(engine) as session:
        statement = select(Tasks).where(Tasks.id == id)
        results = session.exec(statement).first()
        return results

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





# Elimina la tarea con id especifico
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id:int):
    found = False
    for index, task in enumerate(task_list):
        if task.id == id:
            del task_list[index]
            found = True
    
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"Error":"No se ha encontrado la tarea"})
    
    return {"La tarea se ha eliminado"}

# Funcion de busqueda
def search_task(id: int):
    task_searched = filter(lambda task: task.id == id, task_list)
    try:    
        return list(task_searched)[0]
    except:
        return {"error":"No se ha encontrado el usuario"}