import asyncio
import os
from concurrent.futures import ProcessPoolExecutor


from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.core.states import Uniquilizer
from bot.functions import video_uniqueizer, image_uniqueizer


unique_media_router = Router()
uniqualization_semaphore = asyncio.Semaphore(2)


@unique_media_router.message(F.text == __('🕶️ Унікалізувати фото чи відео'))
async def unique_ask_media(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardBuilder()
    kb.button(text=_('🏠 В меню'))

    await message.answer(_('Відправте фото або відео для унікалізації\n\nФормат: jpg, jpeg, png, mp4\nРозмір: до 20 мб'),
                         reply_markup=kb.as_markup(resize_keyboard=True))
    await state.set_state(Uniquilizer.media_input)


@unique_media_router.message(Uniquilizer.media_input)
async def unique_save_media(message: types.Message, state: FSMContext):
    bot = message.bot
    if message.photo:
        photo_id = message.photo[-1].file_id
        file_unique_id = message.photo[-1].file_unique_id
        photo_file = await bot.get_file(photo_id)
        file_path = photo_file.file_path

        os.makedirs(f'./downloads/{file_unique_id}', exist_ok=True)
        await bot.download_file(file_path, f'./downloads/{file_unique_id}/{file_unique_id}.jpg')
        await state.update_data({'photo_path': f'./downloads/{file_unique_id}/{file_unique_id}.jpg'})
    elif message.video:
        video_id = message.video.file_id
        file_unique_id = message.video.file_unique_id
        video_file = await bot.get_file(video_id)
        file_path = video_file.file_path

        os.makedirs(f'./downloads/{file_unique_id}', exist_ok=True)
        await bot.download_file(file_path, f'./downloads/{file_unique_id}/{file_unique_id}.mp4')
        await state.update_data({'video_path': f'./downloads/{file_unique_id}/{file_unique_id}.mp4'})
    elif message.document:
        doc_id = message.document.file_id
        file_unique_id = message.document.file_unique_id

        if message.document.file_size > 20 * 1024 * 1024:
            await message.answer(_('Файл занадто великий, максимальний розмір 20 мб, виберіть інший файл'))
            return

        doc_file = await bot.get_file(doc_id)
        file_path = doc_file.file_path
        file_name = message.document.file_name

        if file_name.lower().endswith('.jpg') or file_name.lower().endswith('.jpeg') or file_name.lower().endswith('.png'):
            os.makedirs(f'./downloads/{file_unique_id}', exist_ok=True)
            await bot.download_file(file_path, f'./downloads/{file_unique_id}/{file_name}')
            await state.update_data({'photo_path': f'./downloads/{file_unique_id}/{file_name}'})

        elif file_name.lower().endswith('.mp4') or file_name.lower().endswith('.mov'):
            os.makedirs(f'./downloads/{file_unique_id}', exist_ok=True)
            await bot.download_file(file_path, f'./downloads/{file_unique_id}/{file_name}')
            await state.update_data({'video_path': f'./downloads/{file_unique_id}/{file_name}'})
        else:
            await message.answer(_('Непідтримуваний формат, повторіть'))
            return

    else:
        await message.answer(_('Відправте фото або відео для унікалізації'))
        return

    await message.answer(_('Введіть кількість унікальних копій для генерації\n(1-20 для фото; 1-5 для відео): \n(Буде згенеровано макс. 50 мб zip файл)'))
    await state.set_state(Uniquilizer.copies_num)


@unique_media_router.message(Uniquilizer.copies_num)
async def unique_num_copies(message: types.Message, state: FSMContext):
    data = await state.get_data()

    media_type = 'photo' if 'photo_path' in data else 'video'

    unique_ask_copies = _('Введіть кількість унікальних копій для генерації\n(1-20 для фото; 1-5 для відео): \n(Буде згенеровано макс. 50 мб zip файл)')
    if not message.text.isdigit():
        await message.answer(unique_ask_copies)
        return
    if media_type == 'photo' and int(message.text) > 20 or int(message.text) < 1:
        await message.answer(unique_ask_copies)
        return
    elif media_type == 'video' and int(message.text) > 5 or int(message.text) < 1:
        await message.answer(unique_ask_copies)
        return

    copies = int(message.text)

    await state.update_data({'copies': copies})
    await message.answer(_('⏳ Зачекайте, генерація додана до черги\n\nФайл буде готовий протягом 1-2 хвилин'))
    await state.set_state(Uniquilizer.generating)
    await unique_generate(message, state)


@unique_media_router.message(Uniquilizer.generating)
async def unique_generate(message: types.Message, state: FSMContext):
    async with uniqualization_semaphore:
        state_data = await state.get_data()
        copies = state_data['copies']

        if 'video_path' in state_data:
            media_path = state_data['video_path']

            with ProcessPoolExecutor(max_workers=10) as executor:
                loop = asyncio.get_event_loop()
                zip_buffer = await loop.run_in_executor(executor, video_uniqueizer.unique_video_generator, media_path, copies)

        elif 'photo_path' in state_data:
            media_path = state_data['photo_path']

            with ProcessPoolExecutor(max_workers=10) as executor:
                loop = asyncio.get_event_loop()
                zip_buffer = await loop.run_in_executor(executor, image_uniqueizer.unique_img_generator, media_path, copies)

        input_file = types.BufferedInputFile(zip_buffer.getvalue(), zip_buffer.name)
        await message.answer_document(input_file)

        import shutil
        shutil.rmtree(os.path.dirname(media_path))

        await state.clear()