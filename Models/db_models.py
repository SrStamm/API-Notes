from sqlmodel import Field, SQLModel

class Users(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    username : str
    email : str
    disabled : bool = Field(default=False)
    password : str

    model_config = {
        "json_schema_extra" : {
            "examples" : [
                {
                    "user_id" : 1,
                    "username" : "user",
                    "email" : "user@mail.com",
                    "disabled" : False,
                    "password" : "1234560"
                }
            ]
        }
    }

class UserRead(SQLModel):
    username : str
    email : str

class Tasks(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text : str

class TaskRead(SQLModel):
    text : str