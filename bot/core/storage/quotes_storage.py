from sqlalchemy import Column, Integer, Text, DateTime, func, create_engine, or_, and_
from sqlalchemy.orm import declarative_base
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///./quotes.sqlite')
# sync_engine = create_engine('sqlite:///../quotes.sqlite')

class UAQuotes(Base):
    __tablename__ = 'ua_quotes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote = Column(Text)

class RUQuotes(Base):
    __tablename__ = 'ru_quotes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote = Column(Text)

class ENQuotes(Base):
    __tablename__ = 'en_quotes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote = Column(Text)


async def get_random_quotes(lang, n_quotes):
    async with AsyncSession(engine) as session:
        if lang == 'uk_UA':
            quote = await session.execute(sa.select(UAQuotes.quote).order_by(func.random()).limit(n_quotes))
        elif lang == 'ru_RU':
            quote = await session.execute(sa.select(RUQuotes.quote).order_by(func.random()).limit(n_quotes))
        else:
            quote = await session.execute(sa.select(ENQuotes.quote).order_by(func.random()).limit(n_quotes))
        return quote.scalars().all()



