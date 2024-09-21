import asyncio
import config

from botcore.bot import ArbitrageBot

async def main():

    bot = ArbitrageBot(token=config.TOKEN)

    await bot.check_apps_task()
    await bot.rotate_proxy_task(config.PROXY_ROTATE)
    await bot.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
