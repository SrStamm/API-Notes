from sqlmodel import Session, SQLModel, create_engine, select, or_
from Models.db_models import Users, Tasks

# sqlite_file_name = "C:\\Users\\Mirko Alexander\\Desktop\\Backend\\to-do\\DB\\database.sqlite"
# sqlite_url = f"sqlite:///{sqlite_file_name}"
# engine = create_engine(sqlite_url, echo=True)

postgres_url = "postgresql://postgres:lubu19$@localhost:5432/mydatabase"
engine = create_engine(postgres_url, echo=True)

def create_db_and_tables():
#    SQLModel.metadata.create_all(engine)
    try:
        engine = create_engine(postgres_url, echo=True)
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print(f"Connected to PostgreSQL: {result.fetchone()}")
    except Exception as e:
        print(f"Error connecting to the database: {e}")

def get_session():
    session = Session(engine)
    try:
        yield session
    except Exception as e:  # Atrapa la excepcion y le da un nombre
        session.close() # Cierra la sesion por el error
        print(f"Database error in get_session: {e}") 
        raise  

    finally: 
        session.close()