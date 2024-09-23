
from sqlalchemy import Column, Integer, Text, func
from sqlalchemy.orm import declarative_base
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///./usersMY.sqlite')

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(Integer)
    two_fa_keys = Column(Text)
    bot_lang = Column(Text)

class Apps(Base):
    __tablename__ = 'apps'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    name = Column(Text)
    url = Column(Text)
    status = Column(Text)

### USERS
async def find_user(tg_id):
    async with AsyncSession(engine) as session:
        user = await session.execute(sa.select(Users.id).where(Users.tg_id == tg_id))
        return user.scalar()

async def add_user(tg_id):
    async with AsyncSession(engine) as session:
        user = Users(tg_id=tg_id)
        session.add(user)
        await session.commit()


async def add_key(tg_id, key):
    async with AsyncSession(engine) as session:
        current_keys = await session.execute(sa.select(Users.two_fa_keys).where(Users.tg_id == tg_id))
        current_keys = current_keys.scalar()
        current_keys = current_keys.split(' ') if current_keys else []

        if key not in current_keys:
            if len(current_keys) == 3:
                current_keys.pop(0)
            current_keys.append(key)

        keys_str = ' '.join(current_keys)

        await session.execute(sa.update(Users).where(Users.tg_id == tg_id).values(two_fa_keys=keys_str))
        await session.commit()


async def get_keys(tg_id):
    async with AsyncSession(engine) as session:
        keys = await session.execute(sa.select(Users.two_fa_keys).where(Users.tg_id == tg_id))
        return keys.scalar()


async def set_lang(tg_id, lang):
    async with AsyncSession(engine) as session:
        await session.execute(sa.update(Users).where(Users.tg_id == tg_id).values(bot_lang=lang))
        await session.commit()

async def get_lang(tg_id):
    async with AsyncSession(engine) as session:
        lang = await session.execute(sa.select(Users.bot_lang).where(Users.tg_id == tg_id))
        return lang.scalar()


### APPS

async def get_all_apps():
    async with AsyncSession(engine) as session:
        apps = await session.execute(sa.select(Apps))
        return apps.scalars().all()

async def get_user_apps(user_id):
    async with AsyncSession(engine) as session:
        apps = await session.execute(sa.select(Apps).where(Apps.user_id == user_id))
        return apps.scalars().all()

async def count_user_apps(user_id):
    async with AsyncSession(engine) as session:
        count = await session.execute(sa.select(func.count()).where(Apps.user_id == user_id))
        return count.scalar()

async def find_app_by_url(user_id, url):
    async with AsyncSession(engine) as session:
        app = await session.execute(sa.select(Apps).where(Apps.user_id == user_id, Apps.url == url))
        return app.scalar()

async def find_app_by_name(user_id, name):
    async with AsyncSession(engine) as session:
        app = await session.execute(sa.select(Apps).where(Apps.user_id == user_id, Apps.name == name))
        return app.scalar()

async def add_app(user_id, url, name):
    async with AsyncSession(engine) as session:
        await session.execute(sa.insert(Apps).values(user_id=user_id, url=url, name=name, status='pending'))
        await session.commit()

async def delete_app(user_id, name):
    async with AsyncSession(engine) as session:
        await session.execute(sa.delete(Apps).where(Apps.user_id == user_id, Apps.name == name))
        await session.commit()

async def update_app_status(user_id, name, status):
    async with AsyncSession(engine) as session:
        await session.execute(sa.update(Apps).where(Apps.user_id == user_id, Apps.name == name).values(status=status))
        await session.commit()





