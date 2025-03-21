import os

from dotenv import load_dotenv, find_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text, URL

load_dotenv(find_dotenv())

POSTGRES_URL = URL.create(
    drivername='postgresql+asyncpg',
    username=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    database=os.getenv('POSTGRES_DB')
)

Base = declarative_base()

engine = create_async_engine(POSTGRES_URL, connect_args={"timeout": 30})
async_session_main = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


async def tmain():
    try:
        # Перевірка підключення
        async with engine.connect() as connection:
            # Використання текстового SQL-запиту
            await connection.execute(text("SELECT 1"))
            print("Успішне підключення до бази даних!")
    except Exception as e:
        print(f"Помилка підключення: {e}")
    finally:
        # Закриття двигуна
        await engine.dispose()


async def create_tables():
    async with engine.begin() as conn:
        # Створення всіх таблиць, визначених у моделі
        await conn.run_sync(Base.metadata.create_all)
        print("Таблиці успішно створені")
