from sqlmodel import Session, SQLModel, create_engine, select, or_
from Models.db_models import Users, Notes, Sessions

postgres_url = "postgresql://postgres:lubu19$@localhost:5432/mydatabase"
engine = create_engine(postgres_url, echo=True, pool_pre_ping=True)

def create_db_and_tables():
#    SQLModel.metadata.create_all(engine)
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print(f"Connected to PostgreSQL: {result.fetchone()}")
    except Exception as e:
        raise {"Error connecting to the database":{e}}

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


import redis

red = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True,
    socket_connect_timeout=3,
    retry_on_timeout=True,
    health_check_interval=30
)