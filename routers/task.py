import logging
from fastapi import APIRouter, status, HTTPException, Depends, Path
from sqlalchemy.exc import SQLAlchemyError
from Models.db_models import Tasks, TaskRead, TaskUpdate, Users, Tags
from DB.database import Session, get_session, select
from routers.auth import current_user, require_admin
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Router de la app
router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", status_code=status.HTTP_200_OK)
def get_tasks_user(user = Depends(current_user), session : Session = Depends(get_session)) -> list[TaskRead]:
    try:
        # Al tener Relationship se puede acceder al task de dos formas:
            # user_found = session.get(Users, user.user_id)
            # results = user_found.tasks
        # Y de la siguiente forma
        statement = select(Tasks).where(Tasks.user_id == user.user_id)
        results = session.exec(statement).all()
        return results
    except SQLAlchemyError as e:
        logger.error(f"Error en get_tasks_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.get("/all")
def get_tasks_all(user: Users = Depends(require_admin), session : Session = Depends(get_session),
                   skip : int = 10, offset : int = 0) -> list[Tasks]:
    
    try:
        statement = select(Tasks).limit(skip).offset(offset)
        results = session.exec(statement).all()
        return results
    except SQLAlchemyError as e:
        logger.error(f"Error en get_tasks_all: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.get("/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=TaskRead)
def tasks_search_id(id: int, user=Depends(current_user), session : Session = Depends(get_session)) -> TaskRead:
    try:
        # Hay dos formas de obtener el task:
        result = session.get(Tasks, id)

        # O la siguiente forma:
            # statement = select(Tasks).where(Tasks.id == id, Tasks.user_id == user.user_id)
            # result = session.exec(statement).first()
        
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la tarea.")
        return result
    
    except SQLAlchemyError as e:
        logger.error(f"Error en tasks_search_id: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(task: Tasks, user=Depends(current_user), session : Session = Depends(get_session)):
    try:
        task = Tasks(**task.model_dump(exclude={"create_date"}), user=user, create_date=datetime.now())
        session.add(task)
        session.commit()
        return {"detail": "Se creó una nueva tarea."}
    
    except SQLAlchemyError as e:
        logger.error(f"Error en create_task: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al crear la tarea.")

@router.patch("/{id}", status_code=status.HTTP_202_ACCEPTED, description="Actualiza la tarea")
def update_task(id: int, task: TaskUpdate,
                user : Users = Depends(current_user),
                session : Session = Depends(get_session)):
    try:
        statement = select(Tasks).where(Tasks.id == id, Tasks.user_id == user.user_id)
        task_selected = session.exec(statement).first()

        if task_selected is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la tarea.")
        
        task_selected.text = task.text
        task_selected.category = task.category
        
        for key in task.tags:
            result = session.select(Tags).where(Tags.tag == key)
            if result is None:
                session.add(key)
        task_selected.tags = task.tags
        session.commit()
        return {"detail": "Tarea actualizada con éxito"}
    
    except SQLAlchemyError as e:
        logger.error(f"Error en update_task: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error":"Error al actualizar la tarea."})


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int, user=Depends(current_user), session : Session = Depends(get_session)):
    try:
        result = session.get(Tasks, id)

        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la tarea.")

        session.delete(result)
        session.commit()
        return {"detail": "Tarea eliminada exitosamente"}
    
    except SQLAlchemyError as e:
        logger.error(f"Error en delete_task: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar la tarea.")