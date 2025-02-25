from sqlmodel import Field, SQLModel
from datetime import date

class Users(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True, description="Se crea solo")
    username : str
    email : str 
    disabled : bool = Field(default=False, description="Cuenta desactivada")
    password : str 
    permission : bool = Field(default=False, description="Permisos de admin")

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

class Tasks(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text : str
    create_date : date = Field(default=date.today().strftime, description="Fecha de creacion")
    category : str = Field(default="Unknown", description="Tipo de nota para agruparlas")
    user_id : int | None = Field(default=int, foreign_key="users.user_id", description="Relacion con el usuario")
class TaskRead(SQLModel):
    text : str
    category : str = Field(default="Unknown", description="Tipo de nota para agruparlas")