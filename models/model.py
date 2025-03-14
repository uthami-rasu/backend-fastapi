import asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    Boolean,
    text,
    ForeignKey,
    DateTime,
)
from sqlalchemy.future import select
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from sqlalchemy.sql import func

load_dotenv()


#  Use asyncpg for PostgreSQL
DATABASE_URL = os.getenv("DATABASE_ENDPOINT")

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Store hashed password
    is_verified = Column(Boolean, default=False, nullable=False)  # Initially False
    verification_token = Column(String(255), unique=True, nullable=True)  # Store token

    # make a relationship between tables
    tasks = relationship("UserTasks", back_populates="user")


class UserTasks(Base):
    __tablename__ = "user_tasks"

    task_id = Column(String(6), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_modified = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )  # Fix here

    duedate = Column(DateTime(timezone=True), nullable=False, default=func.now())
    is_completed = Column(String(3), nullable=False, default="no")
    is_favor = Column(Boolean, nullable=False, default=False)
    color = Column(String(255), default="blue", nullable=True)

    # Relationship to users table
    user = relationship("User", back_populates="tasks")


class SingletonDB:
    _instance = None

    def __new__(cls, url):
        if cls._instance is None:
            try:
                cls._instance = super().__new__(cls)
                cls._instance.engine = create_async_engine(url, echo=True)
                cls._instance.SessionLocal = sessionmaker(
                    cls._instance.engine, expire_on_commit=False, class_=AsyncSession
                )
            except Exception as e:
                print(f"Database connection failed: {e}")
                cls._instance = None
        return cls._instance

    @asynccontextmanager
    async def get_db(self):
        """Provides an async session with proper cleanup."""
        db_ = self.SessionLocal()
        try:
            yield db_
            await db_.commit()
        except Exception:
            await db_.rollback()
            raise
        finally:
            await db_.close()

    async def create_user(self, dbs, payloads):
        """Create a new user asynchronously."""
        try:
            user = User(**payloads)
            dbs.add(user)
            await dbs.commit()
            await dbs.refresh(user)
            return True
        except IntegrityError:
            await dbs.rollback()
            return False

    async def existing_user(self, dbs: AsyncSession, email: str, return_result=False):
        """Check if user exists asynchronously."""

        # result = await aiosession.execute(
        #     text("SELECT COUNT(*) FROM users WHERE email = :email"),
        #     {"email": email},
        # )

        result = await dbs.execute(select(User).filter(User.email == email))

        user = result.scalar_one_or_none()

        return user if return_result else user is not None


db = SingletonDB(DATABASE_URL)
if db.engine is None:
    raise RuntimeError("Database engine initialization failed!")

async def get_db():
    async with db.get_db() as session:
        yield session


async def init_db():
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
