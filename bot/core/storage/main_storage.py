
from sqlalchemy import Column, Integer, Text, DateTime, func, create_engine, or_, and_
from sqlalchemy.orm import declarative_base
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///./users.sqlite')
# engine = create_engine('sqlite:///.././users.sqlite')

class Users(Base):
    __tablename__ = 'users'

    tg_id = Column(Integer, primary_key=True)
    name = Column(Text)
    surname = Column(Text)
    username = Column(Text)
    tg_language = Column(Text)
    bot_language = Column(Text)
    registered_date = Column(DateTime, default=func.now())


class TwoFaKeys(Base):
    __tablename__ = 'two_fa_keys'

    tg_id = Column(Integer, primary_key=True)
    keys = Column(Text)


class Apps(Base):
    __tablename__ = 'apps'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url_app_id = Column(Text)
    app_name = Column(Text)
    url = Column(Text)
    status = Column(Text)

class AppUsers(Base):
    __tablename__ = 'app_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    app_id = Column(Integer)
    user_id = Column(Integer)


class WelcomeMessages(Base):
    __tablename__ = 'welcome_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    welcome_text = Column(Text)
    welcome_media_id = Column(Text)
    welcome_links = Column(Text)


### USERS
async def find_user(tg_id):
    async with AsyncSession(engine) as session:
        user = await session.execute(sa.select(Users.tg_id).where(Users.tg_id == tg_id))
        return user.scalar()

async def add_user(tg_id, name, surname, username, tg_language):
    async with AsyncSession(engine) as session:
        await session.execute(sa.insert(Users).values(tg_id=tg_id, name=name, surname=surname, username=username, tg_language=tg_language))
        await session.commit()

async def get_users_dump():
    async with AsyncSession(engine) as session:
        users = await session.execute(sa.select(Users))
        return users.scalars().all()

async def get_all_user_ids():
    async with AsyncSession(engine) as session:
        users = await session.execute(sa.select(Users.tg_id))
        return users.scalars().all()

async def get_user_ids_by_lang(bot_lang):
    async with AsyncSession(engine) as session:
        # users = await session.execute(sa.select(Users.tg_id).where(Users.bot_language == bot_lang))
        users = await session.execute(sa.select(Users.tg_id).where(
            or_(
                Users.bot_language == bot_lang,
                and_(Users.bot_language == None, Users.tg_language == bot_lang)
            )
        ))
        return users.scalars().all()


async def add_key(tg_id, key):
    async with AsyncSession(engine) as session:
        user = await session.execute(sa.select(TwoFaKeys.tg_id).where(TwoFaKeys.tg_id == tg_id))

        current_keys = await session.execute(sa.select(TwoFaKeys.keys).where(TwoFaKeys.tg_id == tg_id))
        current_keys = current_keys.scalar()
        current_keys = current_keys.split(' ') if current_keys else []

        if key not in current_keys:
            if len(current_keys) == 3:
                current_keys.pop(0)
            current_keys.append(key)

        keys_str = ' '.join(current_keys)

        if user.scalar():
            await session.execute(sa.update(TwoFaKeys).where(TwoFaKeys.tg_id == tg_id).values(keys=keys_str))
        else:
            await session.execute(sa.insert(TwoFaKeys).values(tg_id=tg_id, keys=keys_str))
        await session.commit()


async def get_keys(tg_id):
    async with AsyncSession(engine) as session:
        keys = await session.execute(sa.select(TwoFaKeys.keys).where(TwoFaKeys.tg_id == tg_id))
        return keys.scalar()


async def set_lang(tg_id, lang):
    async with AsyncSession(engine) as session:
        await session.execute(sa.update(Users).where(Users.tg_id == tg_id).values(bot_language=lang))
        await session.commit()


async def get_lang(tg_id):
    async with AsyncSession(engine) as session:
        lang = await session.execute(sa.select(Users.bot_language).where(Users.tg_id == tg_id))
        return lang.scalar()

async def get_lang_codes():
    async with AsyncSession(engine) as session:
        langs = await session.execute(sa.select(Users.bot_language).distinct().where(Users.bot_language != None))
        return langs.scalars().all()

async def count_users():
    async with AsyncSession(engine) as session:
        count = await session.execute(sa.select(func.count()).select_from(Users))
        return count.scalar()

async def count_users_by_code(language_code=None):
    async with AsyncSession(engine) as session:
        count = await session.execute(sa.select(func.count()).where(Users.bot_language == language_code))
        return count.scalar()


### APPS

async def get_all_apps():
    async with AsyncSession(engine) as session:
        apps = await session.execute(sa.select(Apps))
        return apps.scalars().all()

async def get_user_apps(user_id):
    async with AsyncSession(engine) as session:
        app_ids = await session.execute(sa.select(AppUsers.app_id).where(AppUsers.user_id == user_id))
        app_ids = app_ids.scalars().all()

        apps = await session.execute(sa.select(Apps).where(Apps.id.in_(app_ids)))
        return apps.scalars().all()


async def get_users_of_app(id):
    async with AsyncSession(engine) as session:
        user_ids = await session.execute(sa.select(AppUsers.user_id).where(AppUsers.app_id == id))
        user_ids = user_ids.scalars().all()

        users = await session.execute(sa.select(Users.tg_id).where(Users.tg_id.in_(user_ids)))
        return users.scalars().all()

async def get_app_id_by_url_app_id(url_app_id):
    async with AsyncSession(engine) as session:
        app = await session.execute(sa.select(Apps.id).where(Apps.url_app_id == url_app_id))
        return app.scalar()

async def find_app_by_app_id(app_id, user_id):
    async with AsyncSession(engine) as session:
        app = await session.execute(sa.select(AppUsers).where(AppUsers.app_id == app_id, AppUsers.user_id == user_id))
        return app.scalar()


async def get_app_name(id):
    async with AsyncSession(engine) as session:
        app = await session.execute(sa.select(Apps.app_name).where(Apps.id == id))
        return app.scalar()

async def add_app(url_app_id, app_name, url):
    async with AsyncSession(engine) as session:
        find_existing = await session.execute(sa.select(Apps.id).where(Apps.url_app_id == url_app_id))
        existing = find_existing.scalar()
        if existing:
            return existing
        else:
            new_app_id = await session.execute(sa.insert(Apps).values(url_app_id=url_app_id, app_name=app_name, url=url, status='active').returning(Apps.id))
            await session.commit()
            return new_app_id.scalar()

async def add_app_user(app_id, user_id):
    async with AsyncSession(engine) as session:
        await session.execute(sa.insert(AppUsers).values(app_id=app_id, user_id=user_id))
        await session.commit()

async def delete_app_user(app_id, user_id):
    async with AsyncSession(engine) as session:
        await session.execute(sa.delete(AppUsers).where(AppUsers.app_id == app_id, AppUsers.user_id == user_id))
        await session.commit()

        other_users = await session.execute(sa.select(AppUsers.user_id).where(AppUsers.app_id == app_id))
        other_users = other_users.scalars().all()
        if not other_users:
            await session.execute(sa.delete(Apps).where(Apps.id == app_id))
            await session.commit()


async def update_app_status(app_id, status):
    async with AsyncSession(engine) as session:
        await session.execute(sa.update(Apps).where(Apps.id == app_id).values(status=status))
        await session.commit()


async def get_start_msg():
    async with AsyncSession(engine) as session:
        msg = await session.execute(sa.select(WelcomeMessages).limit(1))
        return msg.scalar()


async def set_start_msg(welcome_text, welcome_media_id, welcome_links):
    async with AsyncSession(engine) as session:
        await session.execute(sa.delete(WelcomeMessages))
        await session.commit()

        await session.execute(sa.insert(WelcomeMessages).values(welcome_text=welcome_text,
                                                                welcome_media_id=welcome_media_id,
                                                                welcome_links=welcome_links))
        await session.commit()

