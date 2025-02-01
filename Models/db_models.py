from sqlmodel import Field, SQLModel

class Users(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    username : str
    email : str
    disabled : bool = Field(default=False)
    password : str

class Tasks(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text : str