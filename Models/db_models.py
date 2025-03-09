from sqlmodel import Field, SQLModel, Relationship
from datetime import date
from typing import List

class Users(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True, nullable=False, description="Se crea solo")
    username : str
    email : str 
    disabled : bool = Field(default=False, description="Cuenta desactivada")
    password : str 
    role : str = Field(default='user', description="Se asigna el rol que se puede tener (admin, user)")

    tasks : List["Tasks"] = Relationship(back_populates="user", cascade_delete=True)

    model_config = {
        "json_schema_extra" : {
            "examples" : [
                {
                    "username" : "user",
                    "email" : "user@mail.com",
                    "password" : "1234560",
                }
            ]
        }
    }

class UserRead(SQLModel):
    user_id : int | None = None
    username : str
    email : str


class UserReadAdmin(SQLModel):
    user_id : int 
    username : str
    email : str
    disabled: bool
    permission: bool
    probando : str | None
class UserUpdate(SQLModel):
    username : str | None = None
    email : str | None = None
    password : str | None = None
    permission: bool | None = None

class tasks_tags_link(SQLModel, table=True):
    task_id : int | None = Field(default=None, foreign_key="tasks.id", primary_key=True)
    tag_id : int | None = Field(default=None, foreign_key="tags.id", primary_key=True)
class Tags(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tag: str
    tasks: List["Tasks"] = Relationship(back_populates="tags", link_model=tasks_tags_link)

class read_tag(SQLModel):
    tag: str

class Tasks(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text : str
    create_date : date = Field(default_factory= date.today, description="Fecha de creacion")
    category : str = Field(default="Unknown", description="Tipo de nota para agruparlas")
    user_id : int | None = Field(default=int, foreign_key="users.user_id", description="Relacion con el usuario", ondelete="CASCADE")

    user: "Users" = Relationship(back_populates="tasks")
    tags: List["Tags"] = Relationship(back_populates="tasks", link_model=tasks_tags_link)

    model_config = {
        "json_schema_extra" : 
        {
            "examples" : 
            [
                {
                    "id" : 0,
                    "text" : "Hello World",
                    "create_date" : "01-01-2000",
                    "category" : "Study",
                    "user_id" : 1,
                    "tags" : ["Study","Easy"]
                    
                }
            ]
        }
    }

class TaskRead(SQLModel):
    id: int
    text : str
    category : str
    tags : list[read_tag]
    user_id: int

    class Config:
        orm_mode = True

class TaskUpdate(SQLModel):
    text: str | None = None
    category: str = "Unknown"
    tags : List[str] = None