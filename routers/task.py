import logging
from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.exc import SQLAlchemyError
from Models.db_models import Tasks, TaskRead
from DB.database import Session, engine, select
from routers.auth import current_user

# Configurar logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Router de la app
router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/")
def get_tasks_user(user=Depends(current_user)):
    try:
        with Session(engine) as session:
            statement = select(Tasks).where(Tasks.user_id == user.user_id)
            results = session.exec(statement).all()
            return results
    except SQLAlchemyError as e:
        logger.error(f"Error en get_tasks_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.get("/all")
def get_tasks_all(user=Depends(current_user)):
    if not user.permission:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autorizado.")

    try:
        with Session(engine) as session:
            statement = select(Tasks)
            results = session.exec(statement).all()
            return results
    except SQLAlchemyError as e:
        logger.error(f"Error en get_tasks_all: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.get("/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=TaskRead)
def tasks_search_id(id: int, user=Depends(current_user)):
    try:
        with Session(engine) as session:
            statement = select(Tasks).where(Tasks.id == id, Tasks.user_id == user.user_id)
            result = session.exec(statement).first()
            
            if result is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la tarea.")
            return result
    except SQLAlchemyError as e:
        logger.error(f"Error en tasks_search_id: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(task: Tasks, user=Depends(current_user)):
    try:
        with Session(engine) as session:
            task.user_id = user.user_id
            session.add(task)
            session.commit()
            session.refresh(task)
        return {"detail": "Se creó una nueva tarea."}
    except SQLAlchemyError as e:
        logger.error(f"Error en create_task: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al crear la tarea.")


@router.put("/{id}", status_code=status.HTTP_202_ACCEPTED)
def update_task(task: Tasks, user=Depends(current_user)):
    try:
        with Session(engine) as session:
            statement = select(Tasks).where(Tasks.id == task.id, Tasks.user_id == user.user_id)
            task_selected = session.exec(statement).first()  # Cambié one() por first()

            if not task_selected:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la tarea.")

            task_selected.text = task.text
            task_selected.title = task.title
            task_selected.category = task.category
            session.commit()
            return {"detail": "Tarea actualizada con éxito"}
    except SQLAlchemyError as e:
        logger.error(f"Error en update_task: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al actualizar la tarea.")


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int, user=Depends(current_user)):
    try:
        with Session(engine) as session:
            statement = select(Tasks).where(Tasks.id == id, Tasks.user_id == user.user_id)
            result = session.exec(statement).first()

            if result is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la tarea.")

            session.delete(result)
            session.commit()
            return {"detail": "Tarea eliminada exitosamente"}
    except SQLAlchemyError as e:
        logger.error(f"Error en delete_task: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar la tarea.")
