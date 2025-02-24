from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import datetime
from fastapi.responses import JSONResponse
import aiosmtplib
from email.message import EmailMessage

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


async def send_email(to_email, link):

    try:
        msg = EmailMessage()

        msg["From"] = "therazz007@gmail.com"
        msg["To"] = to_email
        msg["Subject"] = "Email Verification"
        msg.set_content(f"Click the link to verify your email\n: {link}")

        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            username="therazz007@gmail.com",
            password="pdvygjaahwtrftvz",
            start_tls=True,
        )
        return True
    except Exception as e:
        return False


async def register_user(request: UserRegister):

    if not validate_email(request.email):
        return JSONResponse(
            status_code=404, content={"message": "Please enter Valid Email."}
        )

    otp_token = secrets.token_urlsafe(16)
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
        return JSONResponse(
            status_code=404,
            content={
                "message": "Failed to Send Verification Email",
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "message": "User registered! Check your email to verify your account."
        },
    )
