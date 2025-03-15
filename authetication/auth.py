from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# User imports

from rest_schema import *
from utility import *
from models import *

auth = APIRouter()


@auth.post("/register-user")
async def register_user(request: UserRegister, dbs: AsyncSession = Depends(get_db)):

    user_exists = await db.existing_user(dbs, request.email)
    if user_exists:
        raise HTTPException(status_code=409, detail="User Already Exists")

    if not validate_email(request.email):
        return JSONResponse(status_code=401, content="Please enter Valid Email.")

    token = generate_token()
    hash_pwd = hash_password(request.password)

    payloads = {
        # "id": uuid.uuid4(),
        "username": request.username,
        "email": request.email,
        "password": hash_pwd,
        "verification_token": token,
        "is_verified": False,
    }

    await db.create_user(dbs, payloads=payloads)

    verify_email_status = await send_verification_email(
        request.email, request.username, token
    )

    if not verify_email_status:
        raise HTTPException(
            status_code=500,
            detail="Failed to Send Verification Email",
        )

    return JSONResponse(
        status_code=201,
        content={
            "message": "User registered! Check your email to verify your account."
        },
    )


@auth.post("/verify-email")
async def verify_token(req: VerifyToken, dbs: AsyncSession = Depends(get_db)):
    result = await dbs.execute(
        select(User).filter(User.verification_token == req.token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Unauthorized Access")

    # if user.verification_token != req.token:
    #     raise HTTPException(status_code=401, detail="Invalid Token")

    # Update the user verification status
    user.verification_token = None
    user.is_verified = True
    await dbs.commit()

    return JSONResponse(
        status_code=200,
        content={"message": "Email verified successfully!"},
    )


async def handle_verification_process(*args):

    verify_email_status = await send_verification_email(*args)

    if not verify_email_status:
        raise HTTPException(
            status_code=500,
            detail="Failed to Send Verification Email",
        )
    return JSONResponse(
        status_code=202, content={"message": "Check your email to verify your account."}
    )


@auth.post("/login")
async def login(
    response: Response, req: LoginSchema, dbs: AsyncSession = Depends(get_db)
):
    """
    Login endpoint:
    - If the credentials are valid, a JWT token is created (valid for 1 week)
      and set as an HTTP‑only cookie.
    """

    user = await db.existing_user(dbs=dbs, email=req.email, return_result=True)

    if not user or not validate_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    if not user.is_verified:
        return await handle_verification_process(
            req.email, user.username, user.verification_token
        )
    token = generate_jwt_token(req.email)
    response = JSONResponse(
        status_code=201, content={"user": user.username, "message": "Login Successful"}
    )
    # Set cookie (secure=True should be used with HTTPS)
    response.set_cookie(
        key="taskease_token",
        value=token,
        httponly=True,
        max_age=TOKEN_EXPIRE_IN_DAYS * 60 * 60 * 24,
        secure=True,  # Change to True in production with HTTPS!
        samesite="None",
    )
    return response


@auth.get("/me")
async def get_me(
    user: dict = Depends(get_current_user), dbs: AsyncSession = Depends(get_db)
):
    """
    Auto-login check:
    Returns user details if the JWT cookie is valid.
    """
    user = await db.existing_user(dbs, user["email"], return_result=True)
    username = user.username
    return {"authenticated": True, "user": username}


@auth.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    """
    Logout endpoint: Deletes the authentication cookie.
    """
    response.delete_cookie(
        key="taskease_token",
        httponly=True,
        secure=True,  # Must match token setting
        samesite="None",  # Must match token setting
        path="/",  # Important to match cookie path
    )
    return {"message": "Logged out"}
