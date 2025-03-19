from fastapi import APIRouter, status, HTTPException, Depends, Query
from sqlalchemy.exc import SQLAlchemyError
from Models.db_models import Tasks, TaskRead, TaskUpdate, Users, Tags, tasks_tags_link, TaskReadAdmin
from DB.database import Session, get_session, select
from routers.auth import current_user, require_admin
from datetime import datetime
from sqlmodel import func

import logging
# Configurar logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Router de la app
router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", status_code=status.HTTP_200_OK, description="Obtiene todas las notas del usuario. OBLIGATORIO: text")
def get_tasks_user(
                   user = Depends(current_user),
                   session : Session = Depends(get_session),
                   limit : int = Query(10, description="Indica la cantidad de resultados a recibir"),
                   offset: int = Query(0, description='Indica la cantidad que se van a saltear'),
                   tags_searched: list[str] = Query(default=None, description='Indica una lista de tags para la busqueda'),
                   category_searched: str = Query(default=None, description='Indica una categoria para la busqueda'),
                   order_by_category: str = Query(None, description='Indica si se quiere ordenar por categoria de forma ascendete (ASC) o descendente (DESC)'),
                   order_by_date: str = Query(None, description='Indica si se quiere ordenar por fecha de forma ascendente (ASC) o descendente (DESC)')) -> list[TaskRead]:
    
    try:
        statement = select(Tasks).where(Tasks.user_id == user.user_id)
        
        # -- filtrado por tags
        if tags_searched:
            statement = (statement.join(tasks_tags_link, Tasks.id == tasks_tags_link.task_id)
                         .join(Tags, tasks_tags_link.tag_id == Tags.id)
                         .group_by(Tasks.id)
                         .having(func.count(Tags.id) == len(tags_searched)) # -- Solo las tareas que tengan todos los tags
                         )
       
        # -- filtrado por categoria
        if category_searched:
            statement = statement.where(Tasks.category == category_searched)

        # -- ordena segun la categoria
        if order_by_category:
            # En caso de que se pase un valor distinto a 'ASC', se ordena de forma descendente
            order_func = Tasks.category.asc() if order_by_category.upper() == "ASC" else Tasks.category.desc()
            statement = statement.order_by(order_func)

        # -- ordena segun la fecha de creacion, de forma ascendente o descendente
        if order_by_date:
            order_func = Tasks.create_date.asc() if order_by_date.upper() == "ASC" else Tasks.create_date.desc()
            statement = statement.order_by(order_func)

        # -- Resultados de la busqueda
        results = session.exec(statement.limit(limit).offset(offset)).all()
        
        return results

    except SQLAlchemyError as e:
        logger.error(f"Error en get_tasks_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.get("/admin/all/",
            description="Obtiene todas las notas de todos los usuarios. Requiere permiso de administrador",
            status_code=status.HTTP_200_OK)
def get_tasks_admin_all(
                  user = Depends(require_admin),
                  session : Session = Depends(get_session),
                  limit : int = Query(10, description='Indica el limite de resultados a recibir'),
                  offset : int = Query(0, description='Indica cuantos resultados se va a saltar antes de devolver'),
                  tags_searched: list[str] = Query(None, description='Recibe una lista de tags para la busqueda'),
                  category_searched : str = Query(None, description='Indica la categoria para solo buscar por ese valor'),
                  order_by_date: str = None) -> list[TaskReadAdmin]:

    try:
        statement = select(Tasks).limit(limit).offset(offset)

        # -- filtrado por tags
        if tags_searched:
            statement = statement.join(tasks_tags_link).join(Tags).where(Tags.tag.in_(tags_searched)).group_by(Tasks.id).having(func.count(Tags.id) == len(tags_searched))

        # -- busqueda con categoria designada
        if category_searched:
            statement = statement.where(Tasks.category == category_searched)

        # -- ordena segun la fecha de creacion, de forma ascendente o descendente
        if order_by_date:
            order_func = Tasks.create_date.asc() if order_by_date.upper() == "ASC" else Tasks.create_date.desc()
            statement = statement.order_by(order_func)

        results = session.exec(statement).all()
        return results
    
    except SQLAlchemyError as e:
        logger.error(f"Error en get_tasks_all: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.get("/admin/{id}", status_code=status.HTTP_200_OK, response_model=TaskRead, 
            description="Obtiene la nota con id especifico. Requiere permiso de administrador")
def tasks_search_id_admin(id: int,
                    user = Depends(require_admin),
                    session : Session = Depends(get_session)) -> TaskReadAdmin:
    try:
        result = session.get(Tasks, id)
        
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la tarea.")
        return result

    except SQLAlchemyError as e:
        logger.error(f"Error en tasks_search_id: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.post("/", status_code=status.HTTP_201_CREATED, description="Crea una nueva nota. Necesita tener un 'text' como minimo.")
def create_task(task: Tasks,
                user=Depends(current_user),
                session : Session = Depends(get_session)):
    
    try:
        task = Tasks(**task.model_dump(exclude={"create_date"}),
                     user=user,
                     create_date=datetime.now())
        
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
        
        if task.text:
            task_selected.text = task.text

        if task.category:
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
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al actualizar la tarea.")


@router.delete("/{id}", status_code=status.HTTP_202_ACCEPTED, description="Elimina una tarea con id especifico")
def delete_task(id: int,
                user = Depends(current_user),
                session : Session = Depends(get_session)):

    try:
        result = session.exec(select(Tasks).where(Tasks.id == id, Tasks.user_id == user.user_id)).first()

        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la tarea.")

        session.delete(result)
        session.commit()
        return {"detail": "Tarea eliminada exitosamente"}
    
    except SQLAlchemyError as e:
        logger.error(f"Error en delete_task: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar la tarea.")
    

@router.delete("/admin/{id}", status_code=status.HTTP_202_ACCEPTED, description="Elimina una tarea con id especifico")
def delete_task_admin(id: int,
                user = Depends(require_admin),
                session : Session = Depends(get_session)):

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