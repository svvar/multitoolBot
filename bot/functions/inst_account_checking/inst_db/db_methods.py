from sqlalchemy import desc, select
from .engine import async_session_main


async def _get_active_cookies(table, type_where):
    async with async_session_main() as session:
        try:
            stm = select(table).where(type_where).order_by(desc(table.row_id)).limit(100)

            result = await session.execute(stm)
            result = result.scalars().all()
            if not result:
                return None
            cookies = [cookie.cookies for cookie in result]
            return cookies
        except:
            return None

