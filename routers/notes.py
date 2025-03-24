from fastapi import APIRouter, status, HTTPException, Depends, Query
from sqlalchemy.exc import SQLAlchemyError
from Models.db_models import Notes, NoteRead, NoteUpdate, Users, Tags, notes_tags_link, NoteReadAdmin
from DB.database import Session, get_session, select
from routers.auth import current_user, require_admin
from datetime import datetime
from sqlmodel import func

import logging
# Configurar logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Router de la app
router = APIRouter(prefix="/notes", tags=["Notes"])


@router.get("/", status_code=status.HTTP_200_OK, description="Obtiene todas las notas del usuario. OBLIGATORIO: text")
def get_notes_user(
                   user : Users = Depends(current_user),
                   session : Session = Depends(get_session),
                   limit : int = Query(10, description="Indica la cantidad de resultados a recibir"),
                   offset: int = Query(0, description='Indica la cantidad que se van a saltear'),
                   tags_searched: list[str] = Query(default=None, description='Indica una lista de tags para la busqueda'),
                   category_searched: str | None = Query(default=None, description='Indica una categoria para la busqueda'),
                   order_by_category: str | None = Query(None, description='Indica si se quiere ordenar por categoria de forma ascendete (ASC) o descendente (DESC)'),
                   order_by_date: str | None = Query(None, description='Indica si se quiere ordenar por fecha de forma ascendente (ASC) o descendente (DESC)'),
                   search_text: str | None = Query(None, description='Busqueda por texto')) -> list[NoteRead]:
    
    try:
        statement = select(Notes).where(Notes.user_id == user.user_id)

        # Busqueda por texto
        if search_text:
            statement = statement.where(Notes.text.ilike(f"%{search_text}%"))
        
        # -- filtrado por tags
        if tags_searched:
            for tag in tags_searched:
                subquery = select(notes_tags_link).join(Tags).where(
                    Notes.id == notes_tags_link.note_id,
                    Tags.tag == tag
                ).exists()
                statement = statement.where(subquery)
       
        # -- filtrado por categoria
        if category_searched:
            statement = statement.where(Notes.category == category_searched)

        # -- ordena segun la categoria
        if order_by_category:
            if order_by_category.upper() not in ("ASC", "DESC"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"Parametro incorrecto"})
            
            order_func = Notes.category.asc() if order_by_category.upper() == "ASC" else Notes.category.desc()
            statement = statement.order_by(order_func)

        # -- ordena segun la fecha de creacion, de forma ascendente o descendente
        if order_by_date:
            if order_by_date.upper() not in ("ASC", "DESC"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"Parametro incorrecto"})
            
            order_func = Notes.create_at.asc() if order_by_date.upper() == "ASC" else Notes.create_at.desc()
            statement = statement.order_by(order_func)

        # -- Resultados de la busqueda
        results = session.exec(statement.limit(limit).offset(offset)).all()
        
        return results

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en get_notes_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.get("/admin/all/",
            description="Obtiene todas las notas de todos los usuarios. Requiere permiso de administrador",
            status_code=status.HTTP_200_OK)
def get_notes_admin_all(
                  user: Users = Depends(require_admin),
                  session : Session = Depends(get_session),
                  limit : int = Query(10, description='Indica el limite de resultados a recibir'),
                  offset : int = Query(0, description='Indica cuantos resultados se va a saltar antes de devolver'),
                  tags_searched: list[str] = Query(None, description='Recibe una lista de tags para la busqueda'),
                  category_searched : str | None = Query(None, description='Indica la categoria para solo buscar por ese valor'),
                  order_by_date: str | None = Query(None, description="Ordena por la feccha de creacion"),
                  order_by_category: str | None = Query(None, description="Ordena por la categoria"),
                  search_text: str | None = None) -> list[NoteReadAdmin]:

    try:
        statement = select(Notes)

        # Busqueda por texto
        if search_text:
            statement = statement.where(Notes.text.ilike(f"%{search_text}%"))
        
        # -- filtrado por tags
        if tags_searched:
            for tag in tags_searched:
                subquery = select(notes_tags_link).join(Tags).where(
                    Notes.id == notes_tags_link.note_id,
                    Tags.tag == tag
                ).exists()
                statement = statement.where(subquery).distinct()
        
        # -- busqueda con categoria designada
        if category_searched:
            statement = statement.where(Notes.category == category_searched)

        # -- ordena segun la categoria
        if order_by_category: 
            if order_by_category.upper() not in ("ASC", "DESC"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"Parametro incorrecto"})
            
            order_func = Notes.category.asc() if order_by_category.upper() == "ASC" else Notes.category.desc()
            statement = statement.order_by(order_func)

        # -- ordena segun la fecha de creacion, de forma ascendente o descendente
        if order_by_date: 
            if order_by_date.upper() not in ("ASC", "DESC"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"Parametro incorrecto"})

            order_func = Notes.create_at.asc() if order_by_date.upper() == "ASC" else Notes.create_at.desc()
            statement = statement.order_by(order_func)

        results = session.exec(statement.limit(limit).offset(offset)).all()
        return results
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en get_notes_all: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.get("/admin/{id}", status_code=status.HTTP_200_OK, response_model=NoteRead, 
            description="Obtiene la nota con id especifico. Requiere permiso de administrador")
def notes_search_id_admin(id: int,
                    user: Users = Depends(require_admin),
                    session : Session = Depends(get_session)) -> NoteReadAdmin:
    try:
        result = session.get(Notes, id)
        
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la nota.")
        return result

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en notes_search_id: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")


@router.post("/", status_code=status.HTTP_201_CREATED, description="Crea una nueva nota. Necesita tener un 'text' como minimo.")
def create_notes(note: Notes,
                user : Users = Depends(current_user),
                session : Session = Depends(get_session)):
    
    try:
        note = Notes(**note.model_dump(),
                     user=user,
                     create_at = datetime.now())
        
        session.add(note)
        session.commit()
        return {"detail": "Se creó una nueva nota."}
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en create_notes: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al crear la nota.")

@router.patch("/{id}", status_code=status.HTTP_202_ACCEPTED,
              description="Permite actualizar una nota con id especifico.")
def update_note(
                id: int,
                note: NoteUpdate,
                user : Users = Depends(current_user),
                session : Session = Depends(get_session)):
    
    try:
        statement = select(Notes).where(Notes.id == id, Notes.user_id == user.user_id)
        note_selected = session.exec(statement).first()

        if note_selected is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la nota.")
        
        if note.text:
            note_selected.text = note.text

        if note.category:
            note_selected.category = note.category
        
        if note.tags: # Procesa los tags solo si se proporciona una lista en note.tags
            note_selected.tags.clear()
            for tag_name in note.tags:
                statement_tag = select(Tags).where(Tags.tag == tag_name)
                tag_selected_db = session.exec(statement_tag).first()

                if not tag_selected_db: # Si el tag NO existe en la base de datos
                    tag_selected_db = Tags(tag=tag_name) # Crea un nuevo objeto Tag
                    session.add(tag_selected_db) # Añade el nuevo Tag a la sesión

                note_selected.tags.append(tag_selected_db) # Asocia el Tag (existente o nuevo) a la tarea

        session.commit()
        return {"detail": "Nota actualizada con éxito"}
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en update_note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al actualizar la nota.")


@router.delete("/{id}", status_code=status.HTTP_202_ACCEPTED, description="Elimina una nota con id especifico")
def delete_note(id: int,
                user : Users = Depends(current_user),
                session : Session = Depends(get_session)):

    try:
        result = session.exec(select(Notes).where(Notes.id == id, Notes.user_id == user.user_id)).first()

        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la nota.")

        session.delete(result)
        session.commit()
        return {"detail": "Nota eliminada exitosamente"}
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en delete_note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar la nota.")
    

@router.delete("/admin/{id}", status_code=status.HTTP_202_ACCEPTED, description="Elimina una nota con id especifico")
def delete_note_admin(id: int,
                user : Users = Depends(require_admin),
                session : Session = Depends(get_session)):

    try:
        result = session.get(Notes, id)

        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la nota.")

        session.delete(result)
        session.commit()
        return {"detail": "Nota eliminada exitosamente"}
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en delete_note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar la nota.")