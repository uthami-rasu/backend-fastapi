from models import * 

url = os.getenv("DATABASE_ENDPOINT")
db = SingletonDB(url)


async def get_db():
    async with db.get_db() as session:
        yield session