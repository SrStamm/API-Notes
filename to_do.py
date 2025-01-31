# Crear una API de tareas pendientes

from fastapi import FastAPI, status
from pydantic import BaseModel

# Inicializa la app
app = FastAPI()

# Clase de las notas
class Task(BaseModel): 
    id : int
    texto : str

# Lista de las notas
task_list = [
        Task(id=1, texto="Esto es una nota"),
        Task(id=2, texto="Comprar: Pan, Leche, Huevos"),
        Task(id=3, texto="Despues del colegio, ir a la casa de la abueal")
]

# Base
@app.get("/")
def root():
    return {"Bienvenido! Mira todas las tareas pendientes."}

# Lee todas las tareas
@app.get("/tasks/")
def tasks_all():
    return task_list

# Lee la tarea de id especifico
@app.get("/tasks/{id}")
def tasks_search_id(id: int):
    return search_user(id)

# Crea una nueva tarea
@app.post("/tasks")
def create_task(task : Task):
    task_list.append(task)
    return {"Se creo una nueva tarea"}

# Actualiza un usuario segun su ID
@app.put("/tasks/{id}")
def update_task(task: Task):
    found = False   # Indica si se encontro el usuario

    for index, task_search in enumerate(task_list):
        if task_search.id == task.id:
            task_list[index] = task
            found = True
    
    if not found:
        return {"No se ha encontrado la tarea"}
    else: 
        return {"La tarea se ha actualizado"}


# Elimina la tarea con id especifico
@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id:int):
    found = False
    for index, task in enumerate(task_list):
        if task.id == id:
            del task_list[index]
            found = True
    
    if not found:
        return {"No se ha encontrado la tarea"}
    else: 
        return {"La tarea se ha eliminado"}
    


def search_user(id: int):
    task_searched = filter(lambda task: task.id == id, task_list)
    try:    
        return list(task_searched)[0]
    except:
        return {"error":"No se ha encontrado el usuario"}