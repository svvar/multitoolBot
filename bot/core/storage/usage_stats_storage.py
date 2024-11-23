
from sqlalchemy import Column, Integer, Text, DateTime, func, create_engine, update
from sqlalchemy.orm import declarative_base
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///./statistics.sqlite')
# engine = create_engine('sqlite:///../../../statistics.sqlite')

# class FeaturesUsage(Base):
#     __tablename__ = 'features_usage'
#
#     key = Column(Integer, primary_key=True)
#
#     fb_acc_check = Column(Integer, default=0)
#     two_fa = Column(Integer, default=0)
#     tiktok_downloader = Column(Integer, default=0)
#     play_apps_check = Column(Integer, default=0)
#     id_generator = Column(Integer, default=0)
#     unique_media = Column(Integer, default=0)
#     selfie_generator = Column(Integer, default=0)
#     fb_business_verification = Column(Integer, default=0)
#     tiktok_verification = Column(Integer, default=0)
#     text_rewrite = Column(Integer, default=0)
#     password_generator = Column(Integer, default=0)
#     name_generator = Column(Integer, default=0)
#     fan_page_name_generator = Column(Integer, default=0)
#     fan_page_address_generator = Column(Integer, default=0)
#     fan_page_phone_generator = Column(Integer, default=0)
#     fan_page_quote_generator = Column(Integer, default=0)
#     fan_page_all_generator = Column(Integer, default=0)

class FunctionsUsage(Base):
    __tablename__ = 'functions_usage'

    id = Column(Integer, primary_key=True, autoincrement=True)
    function_name = Column(Text)
    usage_count = Column(Integer, default=0)


async def get_usage_stats():
    async with AsyncSession(engine) as session:
        stats = await session.execute(sa.select(FunctionsUsage))
        return stats.scalars().all()


async def update_usage_stats(all_stats_dict: dict):
    async with AsyncSession(engine) as session:
        for key, value in all_stats_dict.items():

            await session.execute(update(FunctionsUsage)
                                  .where(FunctionsUsage.function_name == key)
                                  .values(usage_count=FunctionsUsage.usage_count + value))
        await session.commit()


# async def main():
#     stats = await get_usage_stats()
#
#     print(stats)
#
# if __name__ == '__main__':
#     import asyncio
#     asyncio.run(main())