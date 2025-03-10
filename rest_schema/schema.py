from pydantic import BaseModel
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
