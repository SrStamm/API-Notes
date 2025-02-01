from sqlmodel import Field, SQLModel

class Users(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username : str
    email : str
    age : int
    disabled : bool 
    password : str

class Tasks(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text : str