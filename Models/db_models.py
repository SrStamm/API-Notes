from re import S
from sqlalchemy import table
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from pydantic import EmailStr, field_validator
from typing import List
from enum import Enum
from passlib.context import CryptContext
from uuid import uuid4

import sqlmodel

# Contexto de encriptacion 
crypt = CryptContext(schemes=["bcrypt"])

class Role(str, Enum):
    USER = 'user'
    ADMIN = 'admin'

class Category(str, Enum):
    WORK = 'work'
    STUDY = 'study'
    UNKNOWN = 'unknown'

class Users(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True, nullable=False, description="Se crea solo")
    username : str = Field(index=True)
    email : EmailStr = Field(index=True, description="Correo electronico", unique=True)
    disabled : bool = Field(default=False, description="Se deshabilita el usuario")
    password : str = Field(description="Contraseña del usuario")
    role : Role = Field(default=Role.USER, description="Rol del usuario")

    notes : List["Notes"] = Relationship(back_populates="user", cascade_delete=True)
    session : List["Sessions"] = Relationship(back_populates="user", cascade_delete=True)

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

class notes_tags_link(SQLModel, table=True):
    note_id : int | None = Field(default=None, foreign_key="notes.id", primary_key=True)
    tag_id : int | None = Field(default=None, foreign_key="tags.id", primary_key=True)
class Tags(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tag: str = Field(index=True, unique=True)
    notes: List["Notes"] = Relationship(back_populates="tags", link_model=notes_tags_link)

class Notes(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text : str | None = Field(default=None, description="Texto de la nota")
    create_at : datetime = Field(description="Fecha de creacion")
    category : Category = Field(default=Category.UNKNOWN, description="Tipo de nota para agruparlas")
    user_id : int = Field(foreign_key="users.user_id", index=True, description="Relacion con el usuario", ondelete="CASCADE")

    user: "Users" = Relationship(back_populates="notes")
    tags: List["Tags"] = Relationship(back_populates="notes", link_model=notes_tags_link)

    model_config = {
        "json_schema_extra" : 
        {
            "examples" : 
            [
                {
                    "id" : 0,
                    "text" : "Hello World",
                    "create_at" : "2000-01-01",
                    "category" : "unknown",
                    "user_id" : 1,
                    "tags" : ["Study","Easy"]
                    
                }
            ]
        }
    }

class Sessions(SQLModel, table=True):
    session_id : str = Field(default=lambda:str(uuid4()), primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", index=True, ondelete="CASCADE")
    access_token: str = Field(unique=True)
    refresh_token: str = Field(unique=True)
    access_expires: datetime
    refresh_expires: datetime
    is_active: bool = Field(default=True, nullable=False, index=True)

    user: "Users" = Relationship(back_populates="session")

class shared_notes(SQLModel, table=True):
    original_user_id : int | None = Field(default=None, foreign_key="users.user_id", primary_key=True)
    note_id : int | None = Field(default=None, foreign_key="notes.id", primary_key=True)
    shared_user_id : int | None = Field(default=None, foreign_key="users.user_id", primary_key=True)


class read_session(SQLModel):
    session_id : str
    user_id : int
    is_active : bool

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

class read_tag(SQLModel):
    tag: str

class NoteRead(SQLModel):
    id: int
    text : str
    category : str
    tags : List[read_tag]
    user_id: int

class NoteReadAdmin(SQLModel):
    id: int
    text : str
    create_date : datetime
    category : str
    tags : List[read_tag]
    user_id: int

class NoteUpdate(SQLModel):
    text: str | None = None
    category: str | None = None
    tags : List[str] | None = None

class read_share_note(SQLModel):
    id: int
    text : str
    category : str
    original_user_id: int
    
class shared(SQLModel):
    shared_user_id: int