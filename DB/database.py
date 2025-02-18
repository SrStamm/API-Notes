from sqlmodel import Session, SQLModel, create_engine, select, or_
from Models.db_models import Users, Tasks

sqlite_file_name = "C:\\Users\\Mirko Alexander\\Desktop\\Backend\\to-do\\DB\\database.sqlite"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    session = Session(engine)
    try:
        yield session
    except Exception as e:  # Atrapa la excepcion y le da un nombre
        session.close() # Cierra la sesion por el error
        print(f"Database error in get_session: {e}") # Log the specific error
        raise  # Re-raise the exception after logging and closing the session

    finally: # Ensure session is closed even if no exception occurred
        session.close() # Close the session after use