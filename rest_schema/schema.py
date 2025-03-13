from pydantic import BaseModel
from typing import Optional
from datetime import datetime,timezone
import uuid
from typing import Optional
class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class VerifyToken(BaseModel):
    # email: Optional[str]
    token: str


class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    is_verified: bool
    verification_token: str | None
    password: str

    class Config:
        from_attributes = True


class LoginSchema(BaseModel):
    email: str
    password: str


class Task(BaseModel):
    task_id : str = str(uuid.uuid4())[:6]
    title : str = "No Title"
    description : str = ""
    status : str ="low"
    is_completed:str = "no"
    is_favor:bool = False 
    duedate:datetime = datetime.now(timezone.utc)
    color:str = "blue"


class DeleteTask(BaseModel):

    task_id : str = "" 

class UpdateTask(BaseModel):
    task_id: str 
    title: Optional[str] = None  
    description: Optional[str] = None
    status: Optional[str] = None
    is_completed: Optional[str] = None
    is_favor: Optional[bool] = None
    duedate: Optional[datetime] = None
    color: Optional[str] = None