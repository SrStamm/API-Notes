import logging
from fastapi import APIRouter, status, HTTPException, Depends
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


@router.get("/", status_code=status.HTTP_200_OK,
            description="Obtiene todas las notas del usuario. Puedes usar 'limit' y 'offset' para paginar las notas.\n"
            "Tambien 'order_by_date' para ordenar por fecha de forma ascendente ('ASC') o descendente ('DESC').")
def get_tasks_user(
                   user = Depends(current_user),
                   session : Session = Depends(get_session),
                   limit : int = 10,
                   offset: int = 0,
                   order_by_date: str = None) -> list[TaskRead]:
    try:
        statement = select(Tasks).where(Tasks.user_id == user.user_id).limit(limit).offset(offset)

        # Ordena segun la fecha de creacion, de forma ascendente o descendente
        if order_by_date is not None:
            if order_by_date == 'ASC':
                statement = statement.order_by(Tasks.create_date.asc())
            elif order_by_date == 'DESC':
                statement = statement.order_by(Tasks.create_date.desc())
            else:
                pass
        
        results = session.exec(statement).all()
        return results

    except SQLAlchemyError as e:
        logger.error(f"Error en get_tasks_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.get("/all", description="Obtienes todas las notas de todos los usuarios.\n Requiere permiso de administrador")
def get_tasks_all(
                  user = Depends(require_admin),
                  session : Session = Depends(get_session),
                  skip : int = 10, offset : int = 0) -> list[Tasks]:

    try:
        statement = select(Tasks).limit(skip).offset(offset)
        results = session.exec(statement).all()
        return results
    
    except SQLAlchemyError as e:
        logger.error(f"Error en get_tasks_all: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.get("/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=TaskRead, 
            description="Obtiene la nota con id especifico. Requiere permiso de administrador")
def tasks_search_id(id: int, user = Depends(require_admin), session : Session = Depends(get_session)) -> TaskRead:
    try:
        result = session.get(Tasks, id)
        
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la tarea.")
        return result
    
    except SQLAlchemyError as e:
        logger.error(f"Error en tasks_search_id: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.post("/", status_code=status.HTTP_201_CREATED,
             description="Crea una nueva nota. Necesita tener un 'text' como minimo.")
def create_task(task: Tasks, user=Depends(current_user), session : Session = Depends(get_session)):
    try:
        task = Tasks(**task.model_dump(exclude={"create_date"}), user=user, create_date=datetime.now())
        session.add(task)
        session.commit()
        return {"detail": "Se creó una nueva tarea."}
    
    except SQLAlchemyError as e:
        logger.error(f"Error en create_task: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al crear la tarea.")

@router.patch("/{id}", status_code=status.HTTP_202_ACCEPTED,
              description="Permite actualizar una tarea con id especifico.")
def update_task(
                id: int, task: TaskUpdate,
                user : Users = Depends(current_user),
                session : Session = Depends(get_session)):
    try:
        statement = select(Tasks).where(Tasks.id == id, Tasks.user_id == user.user_id)
        task_selected = session.exec(statement).first()

        if task_selected is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la tarea.")
        
        if task.text is not None:
            task_selected.text = task.text

        if task.category is not None:
            task_selected.category = task.category
        
        if task.tags: # Procesa los tags solo si se proporciona una lista en task.tags
            task_selected.tags.clear()
            for tag_name in task.tags:
                statement_tag = select(Tags).where(Tags.tag == tag_name)
                tag_selected_db = session.exec(statement_tag).first()

                if not tag_selected_db: # Si el tag NO existe en la base de datos
                    tag_selected_db = Tags(tag=tag_name) # Crea un nuevo objeto Tag
                    session.add(tag_selected_db) # Añade el nuevo Tag a la sesión

                task_selected.tags.append(tag_selected_db) # Asocia el Tag (existente o nuevo) a la tarea

        session.commit()
        return {"detail": "Tarea actualizada con éxito"}
    
    except SQLAlchemyError as e:
        logger.error(f"Error en update_task: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error":"Error al actualizar la tarea."})


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, description="Elimina una tarea con id especifico")
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