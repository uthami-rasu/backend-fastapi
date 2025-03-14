from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

# custom modules
from authetication import auth as AuthRouter
from models import *
from authetication.auth import *
from rest_schema import *
from models import task_router as TaskRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs database initialization when the app starts."""
    await init_db()
    yield
    await db.engine.dispose()


app = FastAPI(lifespan=lifespan)

origins = [
    "https://razz-dev.netlify.app",
    "https://*.csb.app",
    "https://nsknlv-3000.csb.app",
    "https://ng2567-3000.csb.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specific frontend origins
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PATCH",
        "PUT",
        "DELETE",
        "OPTIONS",
    ],  # Explicitly allow POST
    allow_headers=["Content-Type", "Authorization"]
)

app.include_router(AuthRouter)
app.include_router(TaskRouter, prefix="/api/tasks")


@app.get("/api/v1/users")
async def get_all_users(dbs: AsyncSession = Depends(get_db)):
    result = await dbs.execute(select(User))
    users = result.scalars().all()

    users_data = [UserSchema.model_validate(user).model_dump() for user in users]

    response_data = {
        "status_code": 200,
        "message": "Users fetched successfully",
        "data": users_data,
    }

    return JSONResponse(status_code=200, content=response_data)


@app.delete("/api/ruin/")
async def delete_all_users(dbs: AsyncSession = Depends(get_db)):

    await dbs.execute(text("TRUNCATE TABLE USERS"))
    await dbs.commit()

    return {"message": "Table Truncated"}


# # method-3


@app.post("/api/test")
async def test(email: str, dbs=Depends(get_db)):

    r = await db.existing_user(dbs, email, True)

    return r


# @app.options("/{full_path:path}")
# async def preflight(full_path: str):
#     return {"message": "Preflight request received."}


# @app.post("/api/auth/verify-token")
# def short_token_verification(request: TokenBody):
#     token = request.token
#     if token not in verification_tokens:
#         raise HTTPException(status_code=404, detail="Invalid Token")

#     data = verification_tokens[token]

#     if datetime.now(timezone.utc) > data["expires_at"]:
#         raise HTTPException(status_code=400, detail="Token Expired")

#     email = data["email"]

#     if email not in db:
#         raise HTTPException(status_code=404, detail="Unauthrized User")

#     db[email]["isVerified"] = True
#     del verification_tokens[token]

#     return JSONResponse(
#         status_code=200, content={"message": "Email Verified Successfully"}
#     )


# def token_verification(token: str):

#     try:
#         # payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#         # email = payload["sub"]
#         # nonce = payload["nonce"]

#         # if nonce in used_tokens:
#         #     raise HTTPException(
#         #         status_code=400, detail={"message": "This token has already been used"}
#         #     )
#         # used_tokens.add(nonce)
#         # if email not in db:
#         #     raise HTTPException(
#         #         status_code=404, detail={"message": "Unauthorized Access"}
#         #     )

#         # if db[email]["token"] != token:
#         #     raise HTTPException(status_code=400, detail={"message": "Invalid Token"})

#         # db[email]["isVerified"] = True
#         # db[email][token] = ""
#         pass

#         return JSONResponse(
#             status_code=201, content={"message": "Email Verified Successfully"}
#         )
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token has expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=400, detail="Invalid token")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
