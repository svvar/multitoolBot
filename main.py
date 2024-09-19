import asyncio
import configparser

from botcore.bot import ArbitrageBot

async def main():
    config = configparser.ConfigParser()
    config.read('config.ini')

    bot = ArbitrageBot(token=config['bot']['token'])

    # await bot.check_apps_task()
    await bot.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
