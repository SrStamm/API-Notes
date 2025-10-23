from sqlmodel import Session, SQLModel, create_engine, select, or_
from Models.db_models import Users, Notes, Sessions
import os
from dotenv import load_dotenv
from alembic import context
import redis
from redis import RedisError

load_dotenv()

# postgres_url = "postgresql://postgres:123456@postgres:5432/mydatabase"
postgres_url = os.getenv("DATABASE_URL")
engine = create_engine(postgres_url, echo=True, pool_pre_ping=True)

if not postgres_url:
    raise ValueError("DATABASE_URL no está definida en el entorno")

config = context.configure

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=SQLModel.metadata
            )
            with context.begin_transaction():
                context.run_migrations()
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

REDIS_URL = os.environ.get('REDIS_URL', "redis://localhost:6379")

red = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=3,
    retry_on_timeout=True,
    health_check_interval=30
)
