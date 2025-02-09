from sqlmodel import Session, SQLModel, create_engine, select, or_
from Models.db_models import Users, Tasks

sqlite_file_name = "C:\\Users\\Mirko Alexander\\Desktop\\Backend\\to-do\\DB\\database.sqlite"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)