import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot.core.states import TikTokDownload
from bot.functions import downloader

tiktok_router = Router()
tiktok_semaphore = asyncio.Semaphore(2)


@tiktok_router.message(F.text == __('📹 Завантажити відео з TikTok'))
async def tiktok_download_start(message: types.Message, state: FSMContext):
    await message.answer(_('Відправте посилання на відео з TikTok'))
    await state.set_state(TikTokDownload.url_input)


@tiktok_router.message(TikTokDownload.url_input)
async def tiktok_download(message: types.Message, state: FSMContext):
    url = message.text
    if 'tiktok.com' not in url:
        await message.answer(_('Непідохдяще посилання, спробуйте ще раз'))
        await state.clear()
        return

    # Clearing state early here to make other commands work correctly while downloading tiktok
    await state.clear()

    await message.answer(_('Зачекайте, відео завантажується...'))

    async with tiktok_semaphore:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=7) as executor:
            download_folder = os.path.abspath('./downloads')
            video_path = await loop.run_in_executor(executor, downloader.save_tiktok_video, url, download_folder)

    if video_path:
        input_file = types.FSInputFile(video_path)
        await message.answer_document(input_file)
        os.remove(video_path)
    else:
        await message.answer(_('Відео не знайдено'))