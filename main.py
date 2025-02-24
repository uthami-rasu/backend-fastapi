from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import datetime
from fastapi.responses import JSONResponse
import aiosmtplib
from email.message import EmailMessage

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


# Define allowed origins (Frontend URL)
origins = [
    "https://ng2567-3000.csb.app/",
    "https://ng2567-3000.csb.app",  # React Dev Server
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allowed domains
    allow_credentials=False,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


import secrets
import re
import json

db = {
    "razz@yopmail.com": {
        "username": "Razz",
        "password": "wdad",
        "token": "q5StCl5J2dT94TiFfKZzxA",
        "isVerified": False,
    }
}


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


import aiosmtplib
from email.message import EmailMessage


async def send_verification_email(recipient_email, user_name, token):
    sender_email = "therazz007@gmail.com"
    verification_link = f"http://localhost:3000/verify-email?token={token}"

    # Create email message
    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = "Verify Your Email"

    # Set plain text fallback
    msg.set_content(
        f"Hello {user_name},\n\nPlease verify your email by clicking the link below:\n{verification_link}"
    )

    # Set HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verification</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 20px auto; background: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1); }
            .header { text-align: center; padding-bottom: 20px; border-bottom: 2px solid #eeeeee; }
            .header h1 { color: #333; font-size: 24px; }
            .content { padding: 20px 0; text-align: center; }
            .content p { font-size: 16px; color: #555; }
            .button-container { text-align: center; margin: 20px 0; }
            .button { display: inline-block; padding: 12px 20px; font-size: 16px; color: #ffffff; background: #007BFF; text-decoration: none; border-radius: 5px; font-weight: bold; }
            .footer { text-align: center; font-size: 14px; color: #777; padding-top: 20px; border-top: 1px solid #eeeeee; }
            .footer a { color: #007BFF; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Email Verification</h1>
            </div>
            <div class="content">
                <p>Hello <strong>{user_name}</strong>,</p>
                <p>Thank you for signing up! Please verify your email by clicking the button below:</p>
                <div class="button-container">
                    <a href="{verification_link}" class="button">Verify Email</a>
                </div>
                <p>If you didn’t request this, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>Need help? Contact us at <a href="mailto:support@example.com">support@example.com</a></p>
                <p>&copy; 2025 Your Company. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """.replace(
        "{user_name}", user_name
    ).replace(
        "{verification_link}", verification_link
    )

    msg.add_alternative(html_content, subtype="html")

    # SMTP Configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "therazz007@gmail.com"
    smtp_password = "pdvygjaahwtrftvz"

    try:
        await aiosmtplib.send(
            msg,
            hostname=smtp_server,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=False,
            start_tls=True,
        )
        return True
    except Exception as e:
        return False


@app.post("/api/v1/register-user")
async def register_user(request: UserRegister):

    if request.email in db:
        pass

    if not validate_email(request.email):
        return JSONResponse(
            status_code=404, content={"message": "Please enter Valid Email."}
        )

    token = secrets.token_urlsafe(4)
    db[request.email] = {
        "username": request.username,
        "password": request.password,
        "token": token,
        "isVerified": False,
    }

    verify_email_status = await send_verification_email(
        request.email, request.username, token
    )

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


# method-2
@app.get("/api/v1/users")
def get_all_users():
    return JSONResponse(status_code=201, content=db)


# method-3
@app.get("/api/auth/verify-token")
def token_verification(token: str):

    for email, user in db.items():
        if user["token"] == token:
            db[email]["isVerified"] = True

        return JSONResponse(
            status_code=201, content={"message": "Email Verified Successfully"}
        )

    return HTTPException(status_code=404, detail={"Invalid or Expired Token"})
