import os
import asyncio

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.utils.i18n import I18n

from bot.core.config import TOKEN
from bot.core.middlewares import DatabaseI18nMiddleware
from bot.routers import (fb_acc_check, two_fa, tiktok_download, id_generator, unique_media,
                         selfie_generator, play_apps, admin, for_farmers, doc_verification, text_rewrite, inst_acc_check)
from bot import main_menu
from bot.routers.play_apps import check_apps_task
from bot.core.usage_statistics import dump_statistics_task, dump_statistics

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def start_polling(bot, dp):
    print('Starting bot')
    await dp.start_polling(bot)


async def main():
    if not os.path.exists('downloads'):
        os.mkdir('downloads')

    i18n = I18n(path='locales', default_locale='ru', domain='messages')
    dp.update.middleware(DatabaseI18nMiddleware(i18n))

    dp.include_router(main_menu.main_menu_router)
    dp.include_router(fb_acc_check.acc_check_router)
    dp.include_router(inst_acc_check.inst_check_router)
    dp.include_router(two_fa.two_fa_router)
    dp.include_router(tiktok_download.tiktok_router)
    dp.include_router(play_apps.play_apps_router)
    dp.include_router(id_generator.id_generator_router)
    dp.include_router(unique_media.unique_media_router)
    dp.include_router(selfie_generator.selfie_gen_router)
    dp.include_router(admin.admin_router)
    dp.include_router(for_farmers.farmers_router)
    dp.include_router(doc_verification.doc_verification_router)
    dp.include_router(text_rewrite.rewrite_router)

    http_session = aiohttp.ClientSession()

    bot.http_session = http_session

    await check_apps_task(bot)
    await dump_statistics_task()
    await start_polling(bot, dp)


@dp.shutdown()
async def on_shutdown(*args, **kwargs):
    await dump_statistics()
    await bot.http_session.close()


if __name__ == '__main__':
    asyncio.run(main())
