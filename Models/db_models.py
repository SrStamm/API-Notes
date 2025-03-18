from sqlmodel import Field, SQLModel, Relationship
from datetime import date
from pydantic import EmailStr, field_validator
from typing import List
from enum import Enum
from passlib.context import CryptContext

# Contexto de encriptacion 
crypt = CryptContext(schemes=["bcrypt"])

class Role(str, Enum):
    USER = 'user'
    ADMIN = 'admin'

class Users(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True, nullable=False, description="Se crea solo")
    username : str = Field(index=True)
    email : EmailStr = Field(index=True, description="Correo electronico", unique=True)
    disabled : bool = Field(default=False, description="Se deshabilita el usuario")
    password : str = Field(description="Contraseña del usuario")
    role : Role = Field(default=Role.USER, description="Rol del usuario")

    tasks : List["Tasks"] = Relationship(back_populates="user", cascade_delete=True)

    def encrypt_password(password : str):
        password = password.encode()
        return crypt.hash(password)
    
    
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

class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("password", check_fields=True)
    def hash_password(cls, value):
        return crypt.hash(value.encode())

class UserRead(SQLModel):
    user_id : int
    username : str
    email : EmailStr

class UserReadAdmin(SQLModel):
    user_id : int 
    username : str
    email : EmailStr
    disabled: bool
    role: str
class UserUpdate(SQLModel):
    username : str | None = None
    email : EmailStr | None = None
    password : str | None = None

class UserUpdateAdmin(SQLModel):
    username : str | None = None
    email : EmailStr | None = None
    password : str | None = None
    role : str | None = None
    disabled: bool | None = None

class tasks_tags_link(SQLModel, table=True):
    task_id : int | None = Field(default=None, foreign_key="tasks.id", primary_key=True)
    tag_id : int | None = Field(default=None, foreign_key="tags.id", primary_key=True)
class Tags(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tag: str = Field(index=True, unique=True)
    tasks: List["Tasks"] = Relationship(back_populates="tags", link_model=tasks_tags_link)

class read_tag(SQLModel):
    tag: str

class Tasks(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text : str = Field(description="Texto de la tarea")
    create_date : date = Field(default_factory= date.today, description="Fecha de creacion")
    category : str = Field(default="Unknown", description="Tipo de nota para agruparlas")
    user_id : int = Field(foreign_key="users.user_id", index=True, description="Relacion con el usuario", ondelete="CASCADE")

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
                    "create_date" : "2000-01-01",
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
    tags : List[read_tag]
    user_id: int

class TaskUpdate(SQLModel):
    text: str | None = None
    category: str | None = None
    tags : List[str] | None = None