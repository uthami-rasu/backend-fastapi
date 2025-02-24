from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import datetime
from fastapi.responses import JSONResponse

app = FastAPI()

import secrets
import re

db = {}


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


async def generate_random_token():
    yield {"token": secrets.token_urlsafe(32)}


async def send_email(to_email, link):
    pass


async def register_user(
    request: UserRegister, generate_token=Depends(generate_random_token)
):

    if not validate_email(request.email):
        return JSONResponse(
            status_code=404, content={"message": "Please enter Valid Email."}
        )

    otp_token = generate_token()
    db[request.email] = {
        "username": request.username,
        "password": request.password,
        "token": otp_token,
        "isVerified": False,
    }

    # Send verification email
    verification_link = f"http://localhost:3000/verify-email?token={otp_token}"
    verify_email_status = await send_email(request.email, verification_link)

    if not verify_email_status:
        pass

    return JSONResponse(
        status_code=200,
        content={
            "message": "User registered! Check your email to verify your account."
        },
    )
