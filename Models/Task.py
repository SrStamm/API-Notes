from pydantic import BaseModel

class Task(BaseModel): 
    id : int
    texto : str
