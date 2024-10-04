import asyncio
import config
import os

from botcore.bot import ArbitrageBot
from botcore.admin import AdminPanel
from aiogram import Bot

async def main():
    if not os.path.exists('downloads'):
        os.mkdir('downloads')

    if not os.path.exists('downloads/admin_welcome'):
        os.mkdir('downloads/admin_welcome')

    tg_bot = Bot(token=config.TOKEN)

    arbitrage_bot = ArbitrageBot(tg_bot)
    admin_panel = AdminPanel(arbitrage_bot)

    arbitrage_bot.include_router(admin_panel.router)

    await arbitrage_bot.check_apps_task()
    await arbitrage_bot.rotate_proxy_task(config.PROXY_ROTATE)
    await arbitrage_bot.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
