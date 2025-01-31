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
        results = session.exec(statement)
        return results

# Crea una nueva tarea
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(task : Task):
    # Verificamos que no exista una tarea con el mismo id
    for index, task_search in enumerate(task_list):
        if task_search.id == task.id:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail={"Ya existe una tarea con este id"})
    
    task_list.append(task)
    return {"Se creo una nueva tarea."}




# Crea una nueva tarea
@router.post("/bd", status_code=status.HTTP_201_CREATED)
def create_task(task : Task):
    db = Session()
    new_task = Tasks(**Task.dict())
    db.add(new_task)
    db.commit()
    return Task.dict()









# Actualiza un usuario segun su ID
@router.put("/{id}", status_code=status.HTTP_202_ACCEPTED)
def update_task(task: Task):
    found = False   # Indica si se encontro el usuario

    for index, task_search in enumerate(task_list):
        if task_search.id == task.id:
            task_list[index] = task
            found = True
    
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"No se ha encontrado la tarea"})
    else: 
        return {"La tarea se ha actualizado"}


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