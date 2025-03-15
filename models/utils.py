import re
import random
import string
from email.message import EmailMessage
import aiosmtplib
import jwt
import secrets
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from fastapi import Request, Response, HTTPException
from dotenv import load_dotenv
import os
from .model import *

# load environment variables
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
TOKEN_EXPIRE_IN_DAYS = 7


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_password(plain_pwd: str, hashed_pwd) -> bool:
    return pwd_context.verify(plain_pwd, hashed_pwd)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


def generate_token(length: int = 6) -> str:
    """Generates a random token of the given length."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


async def send_verification_email(recipient_email, user_name, token):

    verification_link = f"{os.getenv('APP_URL')}?token={token}"

    # Create email message
    msg = EmailMessage()
    msg["From"] = os.getenv("SENDER_EMAIL_ID")
    msg["To"] = recipient_email
    msg["Subject"] = "TaskEase: Verify Your Email"

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
                <p>Need help? Contact us at <a href="mailto:therazz007@gmail.com">razz@gmail.com</a></p>
                <p>&copy; 2025 TaskEase Tech inc. All rights reserved.</p>
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
    # smtp_server = "smtp.gmail.com"
    # smtp_port = 587
    # smtp_username = os.getenv("SENDER_EMAIL_ID")

    try:
        await aiosmtplib.send(
            msg,
            hostname=os.getenv("SMTP_SERVER"),
            port=os.getenv("SMTP_PORT"),
            username=os.getenv("SENDER_EMAIL_ID"),
            password=os.getenv("SENDER_EMAIL_PASSWORD"),
            use_tls=False,
            start_tls=True,
        )
        return True
    except Exception as e:
        print(e)
        return False


def generate_jwt_token(email: str):
    expire = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_IN_DAYS)

    payload = {"sub": email, "expire": expire.timestamp()}

    token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)

    return token


def get_current_user(request: Request):
    token = request.cookies.get("taskease_token")

    print("Token", token)
    print("-----------------------------------------------------------------")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"email": payload.get("sub")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
