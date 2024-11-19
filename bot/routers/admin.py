import io
from datetime import datetime

import validators
import xlsxwriter
from aiogram import types, Router, F, filters
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from bot.core.states import AdminMailing, AdminWelcome
from bot.core.config import ADMINS
from bot.core.storage.main_storage import (get_users_dump, count_users, count_users_by_code, get_lang_codes, get_all_user_ids,
                              get_user_ids_by_lang, set_start_msg)


admin_router = Router()

@admin_router.message(filters.command.Command('admin'))
@admin_router.message(F.text == __('🔙 Назад'))
async def enter_admin_panel(message: types.Message, state: FSMContext):
    await state.clear()

    if message.from_user.id not in ADMINS:
        await message.answer(_('Ви не маєте доступу до цієї команди'))
        return

    admin_kb = ReplyKeyboardBuilder()
    admin_kb.button(text=_('Статистика користувачів'))
    admin_kb.button(text=_('Вигрузити користувачів'))
    admin_kb.button(text=_('Налаштувати розсилку'))
    admin_kb.button(text=_('Налаштувати вітальне повідомлення'))
    admin_kb.button(text=_('🏠 В меню'))
    admin_kb.adjust(2)

    await message.answer(text=_('Панель адміністратора'), reply_markup=admin_kb.as_markup(resize_keyboard=True))


@admin_router.message(F.text == __('Вигрузити користувачів'))
async def dump_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer(_('Ви не маєте доступу до цієї команди'))
        return

    buffer = io.BytesIO()
    buffer.name = f'bot_users_{datetime.now().strftime("%m.%d.%Y")}.xlsx'

    workbook = xlsxwriter.Workbook(buffer)
    worksheet = workbook.add_worksheet()

    format1 = workbook.add_format({'border': 1})
    format2 = workbook.add_format({'border': 2})

    users = await get_users_dump()
    columns = ['tg_id', 'name', 'surname', 'username', 'tg_language', 'bot_language', 'registered_date']

    for col_num, col_name in enumerate(columns):
        worksheet.write(0, col_num, col_name, format2)

    for i, user in enumerate(users, start=1):
        user_list = [user.tg_id, user.name, user.surname, user.username,
                     user.tg_language, user.bot_language, user.registered_date.strftime('%d.%m.%Y %H:%M:%S')]
        for j, value in enumerate(user_list):
            worksheet.write(i, j, value, format1)

    worksheet.autofit()
    workbook.close()
    buffer.seek(0)

    input_doc = types.BufferedInputFile(buffer.getvalue(), filename=buffer.name)
    await message.answer_document(document=input_doc)


@admin_router.message(F.text == __('Статистика користувачів'))
async def show_statistics(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer(_('Ви не маєте доступу до цієї команди'))
        return

    lang_codes = {code: 0 for code in await get_lang_codes()}
    total_users = await count_users()

    for code in lang_codes:
        lang_codes[code] = await count_users_by_code(code)

    text = _('Всього: {} користувачів').format(total_users)
    if lang_codes:
        text += '\n'
        for code, count in lang_codes.items():
            text += '\n'
            text += _('{}: {} користувачів').format(code, count)

    not_set = await count_users_by_code(None)
    text += '\n' + _('Мова не встановлена: {} користувачів').format(not_set)

    await message.answer(text)


@admin_router.message(F.text == __('Налаштувати розсилку'))
async def mailing_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer(_('Ви не маєте доступу до цієї команди'))
        return

    lang_kb = ReplyKeyboardBuilder()
    lang_kb.button(text='uk')
    lang_kb.button(text='ru')
    lang_kb.button(text='en')
    lang_kb.button(text='ALL')
    lang_kb.button(text=_('🔙 Назад'))
    lang_kb.adjust(4)

    await message.answer(_('Виберіть мову для розсилки:'), reply_markup=lang_kb.as_markup(resize_keyboard=True))
    await state.set_state(AdminMailing.selecting_lang)


@admin_router.message(AdminMailing.selecting_lang)
async def mailing_message(message: types.Message, state: FSMContext):
    if message.text not in ['uk', 'ru', 'en', 'ALL']:
        await message.answer(_('Виберіть мову для розсилки:'))
        return

    await state.update_data(lang=message.text)

    kb_back = ReplyKeyboardBuilder()
    kb_back.button(text=_('🔙 Назад'))

    await message.answer(_('Введіть повідомлення для розсилки (1 фото або відео на повідомлення)'),
                         reply_markup=kb_back.as_markup(resize_keyboard=True))

    await state.set_state(AdminMailing.entering_message)


@admin_router.message(AdminMailing.entering_message)
async def mailing_asking_links(message: types.Message, state: FSMContext):
    await state.update_data(message_id=message.message_id)

    kb = ReplyKeyboardBuilder()
    # kb.button(text=ts[lang]['admin_mailing_links'])
    kb.button(text=_('Не додавати посилання'))
    kb.button(text=_('🔙 Назад'))
    kb.adjust(1)

    await message.answer('Введіть список inline-посилань (макс. 3): \n\nФормат:\n*Назва кнопки* *Посилання*\n*Назва кнопки2* *Посилання2*',
                         reply_markup=kb.as_markup(resize_keyboard=True),
                         parse_mode='markdown')

    await state.set_state(AdminMailing.asking_links)

@admin_router.message(AdminMailing.asking_links, F.text == __('Не додавати посилання'))
async def mailing_preview(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data['message_id']

    if 'buttons' in data:
        url_kb = InlineKeyboardBuilder()
        for text, url in data['buttons']:
            url_kb.button(text=text, url=url)

        url_kb.adjust(1)

        await message.bot.copy_message(chat_id=message.chat.id, from_chat_id=message.chat.id, message_id=msg_id,
                                    reply_markup=url_kb.as_markup())
    else:
        await message.bot.copy_message(chat_id=message.chat.id, from_chat_id=message.chat.id, message_id=msg_id)

    ask_mailing_kb = ReplyKeyboardBuilder()
    ask_mailing_kb.button(text=_('Запустити розсилку'))
    ask_mailing_kb.button(text=_('🔙 Назад'))
    ask_mailing_kb.adjust(1)

    await message.answer(_('⬆️Попередній перегляд повідомлення⬆️\n\nЗапустити розсилку?'), reply_markup=ask_mailing_kb.as_markup(resize_keyboard=True))
    await state.set_state(AdminMailing.process)


@admin_router.message(AdminMailing.asking_links)
async def mailing_links(message: types.Message, state: FSMContext):
    if message.text:
        try:
            buttons_result = convert_to_buttons(message.text)
            await state.update_data(buttons=buttons_result)
            await state.set_state(AdminMailing.preview)
            await mailing_preview(message, state)
        except Exception as e:
            await message.answer(_('Неправильний формат вводу посилань, посилання не додані') + '\n\n' + str(e))


@admin_router.message(AdminMailing.process, F.text == __('Запустити розсилку'))
async def mailing_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data['message_id']
    if data['lang'] == 'ALL':
        users = await get_all_user_ids()
    else:
        users = await get_user_ids_by_lang(data['lang'])

    total = len(users)
    successful = 0
    failed = 0

    if message.from_user.id in users:
        users.remove(message.from_user.id)
        total -= 1

    await message.answer(_('Здійснюється розсилка...\nМова: {}').format(data['lang']),
                         reply_markup=types.ReplyKeyboardRemove())
    progress = await message.answer(_('Всього адресатів (окрім ВАС): {}\nУспішно відправлено: {}\nПомилок: {}').format(total, successful, failed))

    mailing_kb = None
    if 'buttons' in data:
        mailing_kb = InlineKeyboardBuilder()
        for text, url in data['buttons']:
            mailing_kb.button(text=text, url=url)
        mailing_kb.adjust(1)

    for user in users:
        try:
            if mailing_kb:
                await message.bot.copy_message(chat_id=user, from_chat_id=message.chat.id, message_id=msg_id,
                                            reply_markup=mailing_kb.as_markup())
            else:
                await message.bot.copy_message(chat_id=user, from_chat_id=message.chat.id, message_id=msg_id)
            successful += 1
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            failed += 1

        if (successful + failed) % 20 == 0 and (successful + failed) != total:
            await progress.edit_text(_('Всього адресатів (окрім ВАС): {}\nУспішно відправлено: {}\nПомилок: {}').format(total, successful, failed))
        if (successful + failed) % total == 0:
            await progress.edit_text(_('Всього адресатів (окрім ВАС): {}\nУспішно відправлено: {}\nПомилок: {}').format(total, successful, failed))

    await message.answer(_('Розсилка завершена'))
    await state.clear()
    await enter_admin_panel(message, state)


@admin_router.message(F.text == __('Налаштувати вітальне повідомлення'))
async def start_message_change(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer(_('Ви не маєте доступу до цієї команди'))
        return

    back_kb = ReplyKeyboardBuilder()
    back_kb.button(text=_('🔙 Назад'))

    await message.answer(_('Введіть нове вітальне повідомлення (+1 фото/відео):\n\nВітальне повідомлення показується усім користувачами при старті бота незалежно від мови'),
                         reply_markup=back_kb.as_markup(resize_keyboard=True))
    await state.set_state(AdminWelcome.entering_message)


@admin_router.message(AdminWelcome.entering_message)
async def start_message_inline_links(message: types.Message, state: FSMContext):
    msg = message.text
    media_id = None
    media_type = None

    if message.photo:
        media_id = message.photo[-1].file_id
        media_type = 'photo'
        msg = message.caption
    elif message.video:
        media_id = message.video.file_id
        media_type = 'video'
        msg = message.caption
    elif message.document:
        await message.answer(_('Відправте медіа не файлом, повторіть'))
        return

    await state.update_data(msg=msg, media_id=media_id, media_type=media_type)

    kb = ReplyKeyboardBuilder()
    kb.button(text=_('Не додавати посилання'))
    kb.button(text=_('🔙 Назад'))

    await message.answer(_('Введіть список inline-посилань (макс. 3): \n\nФормат:\n*Назва кнопки* *Посилання*\n*Назва кнопки2* *Посилання2*'),
                         reply_markup=kb.as_markup(resize_keyboard=True),
                         parse_mode='markdown')
    await state.set_state(AdminWelcome.entering_links)


@admin_router.message(AdminWelcome.entering_links)
async def start_message_saving_links(message: types.Message, state: FSMContext):
    if message.text:
        try:
            buttons_result = convert_to_buttons(message.text)
            await state.update_data(buttons=buttons_result)
        except Exception as e:
            await message.answer(_('Неправильний формат вводу посилань, посилання не додані') + '\n\n' + str(e))

    await start_message_preview(message, state)


@admin_router.message(AdminWelcome.entering_links, F.text == __('Не додавати посилання'))
async def start_message_preview(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg = data['msg']
    media_id = data['media_id']
    media_type = data['media_type']

    url_kb = None

    if 'buttons' in data:
        url_kb = InlineKeyboardBuilder()
        for text, url in data['buttons']:
            url_kb.button(text=text, url=url)

        url_kb.adjust(1)

    if url_kb and media_id:
        if media_type == 'photo':
            await message.answer_photo(photo=media_id, caption=msg, reply_markup=url_kb.as_markup())
        elif media_type == 'video':
            await message.answer_video(video=media_id, caption=msg, reply_markup=url_kb.as_markup())
    elif url_kb:
        await message.answer(msg, reply_markup=url_kb.as_markup())
    elif media_id:
        if media_type == 'photo':
            await message.answer_photo(photo=media_id, caption=msg)
        elif media_type == 'video':
            await message.answer_video(video=media_id, caption=msg)
    else:
        await message.answer(msg)

    save_kb = ReplyKeyboardBuilder()
    save_kb.button(text=_('Зберегти'))
    save_kb.button(text=_('🔙 Назад'))

    await message.answer(_('⬆️Зберегти це повідомлення як стартове?⬆️'),
                         reply_markup=save_kb.as_markup(resize_keyboard=True))
    await state.set_state(AdminWelcome.saving)


@admin_router.message(AdminWelcome.saving, F.text == __('Зберегти'))
async def start_message_save(message: types.Message, state: FSMContext):
    data = await state.get_data()

    msg = data['msg']
    media_id = data['media_id']
    media_type = data['media_type']

    media_id = f'{media_type} {media_id}' if media_id else None
    buttons = None
    if 'buttons' in data:
        buttons = ''
        for text, url in data['buttons']:
            buttons += f'{text} {url}\n'

    await set_start_msg(msg, media_id, buttons)
    await message.answer(_('Вітальне повідомлення збережено'))
    await enter_admin_panel(message, state)

def convert_to_buttons(message_text: str) -> list:
    buttons = message_text.split('\n')
    buttons_result = []

    if len(buttons) > 3:
        buttons = buttons[:3]

    for b in buttons:
        name = b.rsplit(' ', 1)[0].strip(" *")
        url = b.rsplit(' ', 1)[1].strip(" *")
        if validators.url(url):
            buttons_result.append((name, url))
        else:
            raise ValueError(url)

    return buttons_result
