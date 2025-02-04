from sqlmodel import Field, SQLModel

class Users(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    username : str
    email : str
    disabled : bool = Field(default=False)
    password : str
    permission : bool = Field(default=False)

    model_config = {
        "json_schema_extra" : {
            "examples" : [
                {
                    "user_id" : 1,
                    "username" : "user",
                    "email" : "user@mail.com",
                    "disabled" : False,
                    "password" : "1234560",
                    "permission" : False
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
    user_id : int | None = Field(default=int, foreign_key="users.user_id")

class TaskRead(SQLModel):
    text : str