from pydantic import BaseModel

class Task(BaseModel): 
    texto : str
