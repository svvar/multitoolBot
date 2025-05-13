import io
from datetime import datetime

import validators
import xlsxwriter
from aiogram import types, Router, F, filters
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from bot.core.states import AdminMailing, AdminWelcome, BugReport, AdminMsgForward, PinMailingMessage
from bot.core.config import ADMINS
from bot.core.storage.main_storage import (get_users_dump, count_users, count_users_by_code, get_lang_codes,
                                           get_all_user_ids,
                                           get_user_ids_by_lang, set_start_msg, save_mailing_results, get_mailings,
                                           get_mailing_data)
from bot.core.storage.usage_stats_storage import get_usage_stats


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
    admin_kb.button(text=_('Статистика використання'))
    admin_kb.button(text=_('Вигрузити користувачів'))
    admin_kb.button(text=_('Налаштувати розсилку'))
    admin_kb.button(text=_('Переслати повідомлення користувачам'))
    admin_kb.button(text=_('Закріпити повідомлення розсилки'))
    admin_kb.button(text=_('Відкріпити повідомлення розсилки'))
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


@admin_router.message(F.text == __('Статистика використання'))
async def show_usage_statistics(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer(_('Ви не маєте доступу до цієї команди'))
        return

    stats = await get_usage_stats()
    template_string = _('Використання функцій бота:\n\n'
                        'Перевірка акаунтів FB:   *{}*\n'
                        'Перевірка акаунтів Instagram:   *{}*\n'
                        '2fa код:   *{}*\n'
                        'Завантаження відео з TikTok:   *{}*\n'
                        'Перевірка додатків Google Play:   *{}*\n'
                        'Генератор ID:   *{}*\n'
                        'Унікалізація фото/відео:   *{}*\n'
                        'Генератор селфі:   *{}*\n'
                        'Верифікація БМ фейсбук:   *{}*\n'
                        'Верифікація tiktok:   *{}*\n'
                        'Перефразування тексту:   *{}*\n'
                        'Генератор паролів:   *{}*\n'
                        'Генератор імен:   *{}*\n'
                        'Генератор назв fanpage:   *{}*\n'
                        'Генератор адрес fanpage:   *{}*\n'
                        'Генератор телефонів fanpage:   *{}*\n'
                        'Генератор цитат fanpage:   *{}*\n'
                        'Генератор повних fanpage:   *{}*')

    await message.answer(template_string.format(*[stat.usage_count for stat in stats]), parse_mode='markdown')

@admin_router.message(F.text == __('Налаштувати розсилку'))
async def mailing_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer(_('Ви не маєте доступу до цієї команди'))
        return

    back_kb = ReplyKeyboardBuilder()
    back_kb.button(text=_('🔙 Назад'))

    await message.answer(_('Введіть назву розсилки:'), reply_markup=back_kb.as_markup(resize_keyboard=True))
    await state.set_state(AdminMailing.mailing_name_entering)

@admin_router.message(AdminMailing.mailing_name_entering)
async def mailing_lang_choice(message: types.Message, state: FSMContext):
    await state.update_data(mailing_name=message.text)

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

    await message.answer('Введіть список inline-посилань (макс. 3): \n\nФормат:\n*Назва кнопки* *https://link133.com*\n*Назва кнопки2* *https://link233.com*',
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


@admin_router.message(AdminMsgForward.process, F.text == __('Запустити розсилку'))
@admin_router.message(AdminMailing.process, F.text == __('Запустити розсилку'))
async def mailing_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg_id = data['message_id']

    if await state.get_state() == AdminMsgForward.process or data['lang'] == 'ALL':
        users = await get_all_user_ids()
    else:
        users = await get_user_ids_by_lang(data['lang'])

    total = len(users)
    successful = 0
    failed = 0

    if message.from_user.id in users:
        users.remove(message.from_user.id)
        total -= 1

    await message.answer(_('Здійснюється розсилка...\nМова: {}').format(data.get('lang', 'ALL')),
                         reply_markup=types.ReplyKeyboardRemove())
    progress = await message.answer(_('Всього адресатів (окрім ВАС): {}\nУспішно відправлено: {}\nПомилок: {}').format(total, successful, failed))

    mailing_kb = None
    if 'buttons' in data:
        mailing_kb = InlineKeyboardBuilder()
        for text, url in data['buttons']:
            mailing_kb.button(text=text, url=url)
        mailing_kb.adjust(1)


    if await state.get_state() == AdminMailing.process:
        mailing_method = message.bot.copy_message
    else:
        mailing_method = message.bot.forward_message

    chat_data = {}

    for user in users:
        try:
            if mailing_kb:           # forward_message does not support reply_markup, but we don't ask for it in forward dialog | this is unreachable in forward dialog
                sent_msg_id = await mailing_method(chat_id=user, from_chat_id=message.chat.id, message_id=msg_id, reply_markup=mailing_kb.as_markup())
            else:
                sent_msg_id = await mailing_method(chat_id=user, from_chat_id=message.chat.id, message_id=msg_id)
            successful += 1
            chat_data[int(user)] = sent_msg_id.message_id
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            failed += 1

        if (successful + failed) % 20 == 0 and (successful + failed) != total:
            await progress.edit_text(_('Всього адресатів (окрім ВАС): {}\nУспішно відправлено: {}\nПомилок: {}').format(total, successful, failed))
        if (successful + failed) % total == 0:
            await progress.edit_text(_('Всього адресатів (окрім ВАС): {}\nУспішно відправлено: {}\nПомилок: {}').format(total, successful, failed))

    await message.answer(_('Розсилка завершена'))
    await save_mailing_results(data['mailing_name'], chat_data)
    await state.clear()
    await enter_admin_panel(message, state)


@admin_router.message(F.text == __('Переслати повідомлення користувачам'))
async def forward_message_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer(_('Ви не маєте доступу до цієї команди'))
        return

    back_kb = ReplyKeyboardBuilder()
    back_kb.button(text=_('🔙 Назад'))

    await message.answer(_('Введіть назву розсилки:'), reply_markup=back_kb.as_markup(resize_keyboard=True))
    await state.set_state(AdminMsgForward.mailing_name_entering)

@admin_router.message(AdminMsgForward.mailing_name_entering)
async def forward_message_ask_message(message: types.Message, state: FSMContext):
    await state.update_data(mailing_name=message.text)

    await message.answer(_('Перешліть повідомлення, яке потрібно переслати усім користувачам\n'
                           'Буде видно автора повідомлення\n'
                           'Підтримується 1 фото або відео'))
    await state.set_state(AdminMsgForward.waiting_for_message)


@admin_router.message(AdminMsgForward.waiting_for_message)
async def forward_message_submit(message: types.Message, state: FSMContext):
    await state.update_data(message_id=message.message_id)

    ask_mailing_kb = ReplyKeyboardBuilder()
    ask_mailing_kb.button(text=_('Запустити розсилку'))
    ask_mailing_kb.button(text=_('🔙 Назад'))
    ask_mailing_kb.adjust(1)

    await message.answer(_('Підтвердіть пересилку повідомлення усім користувачам'), reply_markup=ask_mailing_kb.as_markup(resize_keyboard=True))
    await state.set_state(AdminMsgForward.process)


@admin_router.message(F.text == __('Закріпити повідомлення розсилки'))
async def pin_message_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer(_('Ви не маєте доступу до цієї команди'))
        return

    back_kb = ReplyKeyboardBuilder()
    back_kb.button(text=_('🔙 Назад'))

    mailings = await get_mailings()
    text = '\n\n'.join([f'{mailing.id} - {mailing.mailing_name}' for mailing in mailings])
    await message.answer(text=text)
    await message.answer(_('Введіть ID розсилки, яку потрібно закріпити'), reply_markup=back_kb.as_markup(resize_keyboard=True))
    await state.set_state(PinMailingMessage.entering_id_for_pin)


@admin_router.message(F.text == __('Відкріпити повідомлення розсилки'))
async def unpin_message_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await message.answer(_('Ви не маєте доступу до цієї команди'))
        return

    back_kb = ReplyKeyboardBuilder()
    back_kb.button(text=_('🔙 Назад'))

    mailings = await get_mailings()
    text = '\n\n'.join([f'{mailing.id} - {mailing.mailing_name}' for mailing in mailings])
    await message.answer(text=text)
    await message.answer(_('Введіть ID розсилки, яку потрібно відкріпити'), reply_markup=back_kb.as_markup(resize_keyboard=True))
    await state.set_state(PinMailingMessage.entering_id_for_unpin)


@admin_router.message(PinMailingMessage.entering_id_for_unpin)
@admin_router.message(PinMailingMessage.entering_id_for_pin)
async def pin_message_process(message: types.Message, state: FSMContext):
    if await state.get_state() == PinMailingMessage.entering_id_for_unpin:
        action_func = message.bot.unpin_chat_message
        progress_msg = _('Всього чатів: {}\nУспішно відкріплено: {}\nПомилок: {}')
    else:
        action_func = message.bot.pin_chat_message
        progress_msg = _('Всього чатів: {}\nУспішно закріплено: {}\nПомилок: {}')

    try:
        mailing_id = int(message.text)
    except ValueError:
        await message.answer(_('Введіть коректний ID розсилки'))
        return

    mailing_data = await get_mailing_data(mailing_id)
    if not mailing_data:
        await message.answer(_('Розсилки з таким ID не існує'))
        return

    total = len(mailing_data)
    successful = 0
    failed = 0
    progress = await message.answer(progress_msg.format(total, successful, failed))


    for user in mailing_data:
        try:
            await action_func(chat_id=int(user), message_id=mailing_data[user])
            successful += 1
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            failed += 1

        if (successful + failed) % 20 == 0 and (successful + failed) != total:
            await progress.edit_text(progress_msg.format(total, successful, failed))
        if (successful + failed) % total == 0:
            await progress.edit_text(progress_msg.format(total, successful, failed))

    await message.answer(_('Закінчено'))
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


##############################################################
# FOR DEVELOPER (send reply to a user that bug/error is fixed)
##############################################################

@admin_router.callback_query(F.data.startswith('bugreport_'))
async def bug_fix_reply(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split('_')[1])
    await state.update_data(user_id=user_id)
    await callback.answer()

    await callback.message.answer(_('Опишіть виправлення помилки (це побачить користувач що повідомив про помилку)'))
    await state.set_state(BugReport.dev_entering_reply)


@admin_router.message(BugReport.dev_entering_reply)
async def bug_fix_reply_send(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']

    text = message.text
    await message.bot.send_message(user_id, text)
    await state.clear()