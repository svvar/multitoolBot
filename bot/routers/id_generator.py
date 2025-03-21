import asyncio
from datetime import datetime
import os
import random
from concurrent.futures import ProcessPoolExecutor


from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.core.usage_statistics import usage
from bot.core.states import IdGenerator
from bot.functions import id_generator


id_generator_router = Router()
id_semaphore = asyncio.Semaphore(2)

@id_generator_router.message(F.text == __('🆔 Генератор ID'))
async def id_gen_start(message: types.Message, state: FSMContext):
    reply_kb = ReplyKeyboardBuilder()
    reply_kb.button(text=_('❌ Метадані не потрібні'))
    reply_kb.button(text=_('🎲 Випадкові метадані'))
    reply_kb.button(text=_('🏠 В меню'))
    reply_kb.button(text=_('🔧🐞 Повідомити про помилку'))
    reply_kb.adjust(2, 1, 1)

    await message.answer(_('Чи потрібні вам метадані фото?'), reply_markup=reply_kb.as_markup(resize_keyboard=True))
    await state.set_state(IdGenerator.need_meta)


@id_generator_router.message(IdGenerator.need_meta)
async def id_gen_photo_ask(message: types.Message, state: FSMContext):
    meta = message.text
    if meta == _('❌ Метадані не потрібні'):
        await state.update_data({'meta': False})
    elif meta == _('🎲 Випадкові метадані'):
        await state.update_data({'meta': True})
    else:
        await message.answer(_('Помилкова відповідь, введіть ще раз коректно'))
        return

    reply_kb = ReplyKeyboardBuilder()
    reply_kb.button(text=_('Випадкове фото'))
    reply_kb.button(text=_('🏠 В меню'))
    reply_kb.button(text=_('🔧🐞 Повідомити про помилку'))
    reply_kb.adjust(1)

    await message.answer(_('Відправте фото або натисніть "Випадкове фото"'), reply_markup=reply_kb.as_markup(resize_keyboard=True))
    await state.set_state(IdGenerator.selecting_photo)


@id_generator_router.message(IdGenerator.selecting_photo)
async def id_gen_color(message: types.Message, state: FSMContext):
    if message.photo:
        photo_id = message.photo[-1].file_id
        photo_file = await message.bot.get_file(photo_id)
        file_unique_id = message.photo[-1].file_unique_id
        file_path = photo_file.file_path

        await message.bot.download_file(file_path, f'./assets/temp/{file_unique_id}.jpg')
        await state.update_data({'photo_path': f'./assets/temp/{file_unique_id}.jpg'})
    elif message.document and message.document.mime_type.startswith('image'):
        photo_id = message.document.file_id
        photo_file = await message.bot.get_file(photo_id)
        file_unique_id = message.document.file_unique_id
        file_name = message.document.file_name
        file_path = photo_file.file_path

        await message.bot.download_file(file_path, f'./assets/temp/{file_unique_id}.{file_name.split(".")[-1]}')
        await state.update_data({'photo_path': f'./assets/temp/{file_unique_id}.{file_name.split(".")[-1]}'})
    elif message.text and message.text == _('Випадкове фото'):
        await state.update_data({'photo_path': None})
    else:
        await message.answer(_('Помилкова відповідь, введіть ще раз коректно'))
        return

    reply_kb = ReplyKeyboardBuilder()
    reply_kb.button(text=_('🎨 Кольорове'))
    reply_kb.button(text=_('⚫⚪ Чорно-біле'))
    reply_kb.button(text=_('🏠 В меню'))
    reply_kb.button(text=_('🔧🐞 Повідомити про помилку'))
    reply_kb.adjust(2, 1, 1)

    await message.answer(_('Виберіть колір фото:'), reply_markup=reply_kb.as_markup(resize_keyboard=True))
    await state.set_state(IdGenerator.selecting_color)


@id_generator_router.message(IdGenerator.selecting_color)
async def id_gen_sex(message: types.Message, state: FSMContext):
    color = message.text
    if color == _('🎨 Кольорове'):
        await state.update_data({'grey': False})
    elif color == _('⚫⚪ Чорно-біле'):
        await state.update_data({'grey': True})
    else:
        await message.answer(_('Помилкова відповідь, введіть ще раз коректно'))
        return

    state_data = await state.get_data()
    if state_data['photo_path']:
        kb = ReplyKeyboardBuilder()
        kb.button(text=_('🏠 В меню'))
        await message.answer(_("Введіть ім'я та прізвище:"), reply_markup=kb.as_markup(resize_keyboard=True))
        await state.set_state(IdGenerator.entering_name)
    else:
        reply_kb = ReplyKeyboardBuilder()
        reply_kb.button(text=_('🕺 Чоловік'))
        reply_kb.button(text=_('💃 Жінка'))
        reply_kb.button(text=_('🏠 В меню'))
        reply_kb.button(text=_('🔧🐞 Повідомити про помилку'))
        reply_kb.adjust(2, 1, 1)

        await message.answer(_('Виберіть стать:'), reply_markup=reply_kb.as_markup(resize_keyboard=True))
        await state.set_state(IdGenerator.selecting_sex)


@id_generator_router.message(IdGenerator.selecting_sex)
async def id_gen_name(message: types.Message, state: FSMContext):
    sex = message.text
    if sex == _('🕺 Чоловік'):
        await state.update_data({'sex': 'male'})
    elif sex == _('💃 Жінка'):
        await state.update_data({'sex': 'female'})
    else:
        await message.answer(_('Помилкова відповідь, введіть ще раз коректно'))
        return

    kb = ReplyKeyboardBuilder()
    kb.button(text=_('🏠 В меню')).button(text=_('🔧🐞 Повідомити про помилку')).adjust(1)
    await message.answer(_("Введіть ім'я та прізвище:"), reply_markup=kb.as_markup(resize_keyboard=True))
    await state.set_state(IdGenerator.entering_name)


@id_generator_router.message(IdGenerator.entering_name)
async def id_gen_age(message: types.Message, state: FSMContext):
    name = message.text.split(' ')
    if len(name) != 2:
        await message.answer(_('Помилкова відповідь, введіть ще раз коректно'))
        return

    await state.update_data({'name': name[0], 'surname': name[1]})

    await message.answer(_('Введіть дату народження (ДД.ММ.РРРР):'))
    await state.set_state(IdGenerator.entering_age)


@id_generator_router.message(IdGenerator.entering_age)
async def id_gen_final(message: types.Message, state: FSMContext):
    age = message.text
    try:
        age = datetime.strptime(age, '%d.%m.%Y')
        usage.id_generator += 1
        await state.update_data({'day': age.day, 'month': age.month, 'year': age.year})
        await state.set_state(IdGenerator.generating)
        await id_generate(message, state)
    except ValueError:
        await message.answer(_('Помилкова відповідь, введіть ще раз коректно'))
        return


@id_generator_router.message(IdGenerator.generating, F.text == __('🔄 Ще один варіант'))
async def id_generate(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardBuilder()
    kb.button(text=_('🏠 В меню')).button(text=_('🔧🐞 Повідомити про помилку')).adjust(1)

    # Enable here if you want to add each generation to usage statistics
    # usage['id_generator'] += 1
    await message.answer(_('⏳ Зачекайте, генерується фото...'), reply_markup=kb.as_markup(resize_keyboard=True))
    stored_data = await state.get_data()
    account = id_generator.Account(stored_data['name'], stored_data['surname'], stored_data['day'], stored_data['month'], stored_data['year'])

    if not stored_data['photo_path']:

        if stored_data['sex'] == 'male':
            photo_dir = './assets/male'
        else:
            photo_dir = './assets/female'

        photo_path = os.path.join(photo_dir, random.choice(os.listdir(photo_dir)))
        kb.button(text=_('🔄 Ще один варіант'))
    else:
        photo_path = stored_data['photo_path']

    result_path = os.path.join('./assets/temp', f'{account.name}_{account.surname}{message.message_id}.jpg')

    async with id_semaphore:
        with ProcessPoolExecutor(max_workers=10) as executor:
            loop = asyncio.get_event_loop()
            if stored_data['photo_path']:
                await loop.run_in_executor(executor, id_generator.detect_face, photo_path)
            await loop.run_in_executor(executor, id_generator.generate_document, account, photo_path, result_path, stored_data['grey'], stored_data['meta'])

    if os.path.exists(result_path):
        input_file = types.FSInputFile(result_path)
        await message.answer_document(input_file, reply_markup=kb.as_markup(resize_keyboard=True))
        os.remove(result_path)
    else:
        await message.answer(_('Помилка генерації'), reply_markup=kb.as_markup(resize_keyboard=True))

    if stored_data['photo_path']:
        os.remove(photo_path)

