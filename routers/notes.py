from fastapi import APIRouter, status, HTTPException, Depends, Query
from sqlalchemy.exc import SQLAlchemyError
from Models.db_models import (Notes, NoteRead, NoteUpdate,
                              Users, Tags, notes_tags_link,
                              NoteReadAdmin, shared_notes,
                              read_share_note, NoteUpdateShare, shared_permission)
from DB.database import Session, get_session, select, red, RedisError
from routers.auth import current_user, require_admin
from datetime import datetime
import json
import logging


# Configurar logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Router de la app
router = APIRouter(prefix="/notes", tags=["Notes"])

# Elimina todas las cachés relacionadas con las notas del usuario
def invalidate_user_notes(user_id: int):
    try:
        # Usar SCAN para evitar bloqueos en producción
        keys = []
        pattern = f"user_notes:{user_id}:*"
        for key in red.scan_iter(pattern):
            keys.append(key)

        if keys:
            red.delete(*keys)

        # Invalidar también notas compartidas
        shared_pattern = f"shared_notes:*:{user_id}:*"
        for key in red.scan_iter(shared_pattern):
            red.delete(key)

    except RedisError as e:
        logger.error(f"Error invalidando cache: {str(e)}")

# Obtener notas personales
@router.get("/personal/", status_code=status.HTTP_200_OK, description="Obtiene todas las notas del usuario. OBLIGATORIO: text")
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

    # Generar clave única considerando todos los parámetros
    params = [
        user.user_id,
        limit,
        offset,
        ','.join(sorted(tags_searched)) if tags_searched else '',
        category_searched or '',
        order_by_category or '',
        order_by_date or '',
        search_text or ''
    ]
    # Se crea la clave
    cache_key = f"user_notes:{':'.join(map(str, params))}"

    try:
        # Intenta obtener del cache
        cached_data = red.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        # Caso contrario, obtiene los datos
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

        # Convertir resultados a Pydantic antes de cachear
        notes_list = [NoteRead.model_validate(note).model_dump() for note in results]
        red.setex(cache_key, 60, json.dumps(notes_list))

        return results

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en get_notes_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")

# Obtener notas compartidas
@router.get("/shared/", status_code=status.HTTP_200_OK, description="Obtiene todas las notas del usuario. OBLIGATORIO: text")
def get_shared_notes_user(
                   user : Users = Depends(current_user),
                   session : Session = Depends(get_session),
                   limit : int = Query(10, description="Indica la cantidad de resultados a recibir"),
                   offset: int = Query(0, description='Indica la cantidad que se van a saltear'),
                   tags_searched: list[str] = Query(default=None, description='Indica una lista de tags para la busqueda'),
                   category_searched: str | None = Query(default=None, description='Indica una categoria para la busqueda'),
                   order_by_category: str | None = Query(None, description='Indica si se quiere ordenar por categoria de forma ascendete (ASC) o descendente (DESC)'),
                   order_by_date: str | None = Query(None, description='Indica si se quiere ordenar por fecha de forma ascendente (ASC) o descendente (DESC)'),
                   search_text: str | None = Query(None, description='Busqueda por texto')) -> list[read_share_note] :

    # Generar clave única considerando todos los parámetros
    params = [
        user.user_id,
        limit,
        offset,
        ','.join(sorted(tags_searched)) if tags_searched else '',
        category_searched or '',
        order_by_category or '',
        order_by_date or '',
        search_text or ''
    ]
    # Se crea la clave
    cache_key = f"shared_notes:{':'.join(map(str, params))}"

    try:
        # Intenta obtener del cache
        cached_data = red.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        statement = (select(shared_notes.original_user_id, shared_notes.note_id, Notes.text, Notes.category)
                     .join(shared_notes, shared_notes.note_id == Notes.id)
                     .where(shared_notes.shared_user_id == user.user_id))

        results = session.exec(statement).all()

        if results is None:
            HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ninguna nota compartida")

        # Busqueda por texto
        if search_text:
            statement = statement.where(Notes.text.ilike(f"%{search_text}%"))
       
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
        
        if results is None:
            HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ninguna nota compartida")

        # Convertir resultados a Pydantic antes de cachear
        notes_list = [read_share_note.model_validate(note).model_dump() for note in results]
        red.setex(cache_key, 60, json.dumps(notes_list))

        return results

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en get_shared_notes_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")

# Obtener todas las notas de todos los usuarios
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

# Obtener una nota de cualquier usuario
@router.get("/admin/{id}", status_code=status.HTTP_200_OK, response_model=NoteRead, 
            description="Obtiene la nota con id especifico. Requiere permiso de administrador")
def notes_search_id_admin(id: int,
                          user: Users = Depends(require_admin),
                          session : Session = Depends(get_session)) -> NoteReadAdmin:
    
    cache_key = f'note:{id}'
    try:
        # Comprueba si hay dato cacheado
        cached_data = red.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
        # Caso no tenga, sigue con su trabajo
        result = session.get(Notes, id)
        
        if result:
            note_data = NoteReadAdmin.model_validate(result).model_dump()
            red.setex(cache_key, 60,  json.dumps(note_data))
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró la nota.")

        return result

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en notes_search_id: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")

# Crea una nueva nota
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
        session.refresh(note)

        # Invalidar cache
        invalidate_user_notes(user.user_id)
        red.delete(f"note:{id}")

        return {"detail": "Se creó una nueva nota", "new_note": note}

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en create_notes: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al crear la nota.")

# Comparte una nota con otro usuario
@router.post("/{note_id}/shared/{shared_user_id}", status_code=status.HTTP_200_OK, description="Comparte una nota ya creada a otro usuario")
async def share_notes(note_id: int,
                shared_user_id: int,
                permission: shared_permission = Query(default=shared_permission.READ),
                user : Users = Depends(current_user),
                session : Session = Depends(get_session)):
    
    try:
        nota = session.get(Notes, note_id)

        if not nota:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota no encontrada")
        
        share_user = session.get(Users, shared_user_id)
        if not share_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota no encontrada")

        statement = (select(Notes)
                     .join(shared_notes, shared_notes.note_id == Notes.id)
                     .join(Users, Users.user_id == shared_notes.original_user_id)
                     .where(Users.user_id == user.user_id, Notes.id == note_id, shared_notes.shared_user_id == shared_user_id))
        
        resultado = session.exec(statement).first()

        if resultado:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya se ha compartido esta nota")
        
        nota_compartida = shared_notes(original_user_id=user.user_id, note_id=note_id, shared_user_id=shared_user_id, permission=permission)
        
        session.add(nota_compartida)
        session.commit()

        return {"detail": "Se compartio la nota."}
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en create_notes: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al crear la nota.")

# Obtener notas compartidas
@router.patch("/shared/{shared_note_id}", status_code=status.HTTP_200_OK, description="Obtiene todas las notas del usuario. OBLIGATORIO: text")
async def patch_shared_notes_user(shared_note_id: int,
                            update_note: NoteUpdateShare,
                            user : Users = Depends(current_user),
                            session : Session = Depends(get_session)):
    
    try:
        statement = (select(shared_notes)
                     .where(shared_notes.shared_user_id == user.user_id, shared_notes.note_id == shared_note_id))
        
        shared_note_selected = session.exec(statement).first()
        
        if not shared_note_selected:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ninguna nota compartida")

        if shared_note_selected.permission == 'read':
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No estas autorizado para modificar esta nota")

        note_selected = session.get(Notes,shared_note_selected.note_id)

        if note_selected is None:
            HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontro ninguna nota")
        
        if update_note.text:
            note_selected.text = update_note.text

        if update_note.category:
            note_selected.category = update_note.category
                
        session.commit()

        return {"detail":"La nota fue actualizada con exito"}

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en get_shared_notes_user: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al acceder a la base de datos.")

# Modifica una nota
@router.patch("/{id}", status_code=status.HTTP_202_ACCEPTED,
              description="Permite actualizar una nota con id especifico.")
async def update_note(
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

        # Invalidar cache
        invalidate_user_notes(user.user_id)
        red.delete(f"note:{id}")

        # Busca si esta nota fue compartida, y la actualiza
        statement = (select(shared_notes)
                     .where(shared_notes.original_user_id == user.user_id, shared_notes.note_id == note_selected.id))

        shared_note_selected = session.exec(statement).first()

        if shared_note_selected:
            shared_user = shared_note_selected.shared_user_id
            session.delete(shared_note_selected)
            session.add(
                shared_notes(
                    original_user_id=user.user_id,
                    note_id=note_selected.id,
                    shared_user_id=shared_user)
            )
            session.commit()

        session.refresh(note_selected)

        return {"detail": "Nota actualizada con éxito", "updated_note": note_selected}

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en update_note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al actualizar la nota.")

# Elimina una nota
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

        # Invalidar cache
        invalidate_user_notes(user.user_id)
        red.delete(f"note:{id}")

        return {"detail": "Nota eliminada exitosamente"}
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en delete_note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar la nota.")
    
# Elimina una nota de cualquier usuario
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

        # Invalidar cache
        invalidate_user_notes(result.user_id)
        red.delete(f"note:{id}")

        return {"detail": "Nota eliminada exitosamente"}
    
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error en delete_note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error al eliminar la nota.")
