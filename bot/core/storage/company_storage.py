from sqlalchemy import Column, Integer, Text, func, insert
from sqlalchemy.orm import declarative_base
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///./companies.sqlite')


class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    registration_date = Column(Text)
    address = Column(Text)
    edrpou = Column(Text)
    registrator = Column(Text)

class USCompany(Base):
    __tablename__ = 'us_companies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    state = Column(Text, nullable=False)


async def save_company(name, registration_date, address, edrpou, registrator):
    async with AsyncSession(engine) as session:
        await session.execute(insert(Company).values(name=name, registration_date=registration_date, address=address, edrpou=edrpou, registrator=registrator))
        await session.commit()


async def get_random_company():
    async with AsyncSession(engine) as session:
        company = await session.execute(sa.select(Company).order_by(func.random()).limit(1))
        return company.scalar()


async def save_us_company(name, address, state):
    async with AsyncSession(engine) as session:
        await session.execute(insert(USCompany).values(name=name, address=address, state=state))
        await session.commit()


async def get_random_us_company():
    async with AsyncSession(engine) as session:
        company = await session.execute(sa.select(USCompany).order_by(func.random()).limit(1))
        return company.scalar()
