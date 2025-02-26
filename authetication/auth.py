from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# User imports
from models import *
from rest_schema import *
from .utils import *

url = "postgresql+psycopg2://razz_kutty:Q5jE2MhNPP4dJtEWwcj2un2Yu0qW3D6z@dpg-cuuu2ktds78s73b516ig-a.singapore-postgres.render.com:5432/razz_dev_users"

db = SingletonDB(url)

auth = APIRouter()


async def get_db():
    async with db.get_db() as session:
        yield session


@auth.post("/api/v1/register-user")
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


@auth.post("/auth/verify-email")
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


def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    print(token, "checking")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"email": payload.get("sub")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@auth.post("/auth/login")
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

    token = generate_jwt_token(req.email)

    response = JSONResponse(status_code=201, content={"message": "Login Successful"})
    # Set cookie (secure=True should be used with HTTPS)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=TOKEN_EXPIRE_IN_DAYS * 60 * 60 * 24,
        secure=True,  # Change to True in production with HTTPS!
        samesite="None",
    )
    return response


@auth.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    """
    Auto-login check:
    Returns user details if the JWT cookie is valid.
    """
    return {"authenticated": True, "user": user}


@auth.post("/auth/logout")
async def logout(response: Response):
    """
    Logout endpoint:
    Deletes the authentication cookie.
    """
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


# ----------------------------
# Protected Router
# ----------------------------
protected_router = APIRouter()


@protected_router.get("/dashboard")
async def dashboard(user: dict = Depends(get_current_user)):
    """
    Protected route:
    Accessible only if the user is authenticated.
    """
    return {"message": f"Welcome {user['email']}! This is your dashboard."}


# ----------------------------
# Include Routers in the App
# ----------------------------
# app.include_router(auth, prefix="/auth")
# app.include_router(protected_router, prefix="/api")
