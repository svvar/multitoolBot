import io

from aiogram import types, Router, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendMediaGroup

from bot.core.states import CheckingAccounts
from bot.core.usage_statistics import usage
from bot.main_menu import show_menu
from bot.functions import account_checking


acc_check_router = Router()


@acc_check_router.message(F.text == __('✅️ Перевірити FB акаунти на блокування'))
async def check_account_blocked(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardBuilder()
    kb.button(text=_('Почати перевірку'))
    kb.button(text=_('🏠 В меню'))
    kb.adjust(1)

    await message.answer(_('Відправте список посилань на акаунти або txt файл з посиланнями\nПотім натисніть "Почати перевірку"'),
                         reply_markup=kb.as_markup(resize_keyboard=True))
    await state.set_state(CheckingAccounts.start_checking)
    await state.update_data({'messages': [], 'txt': None})


@acc_check_router.message(CheckingAccounts.start_checking, F.text == __('Почати перевірку'))
async def check_links(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    messages = '\n'.join(state_data['messages'])
    txt = state_data['txt']

    raw_links = txt if txt else messages

    links = account_checking.extract_links(raw_links)

    active, blocked, errors = await account_checking.check_urls(links)

    message_text = _('*Активних: {}\nЗаблокованих: {}\nПомилок перевірки: {}*').format(len(active), len(blocked), len(errors))
    message_files = []

    if len(active) <= 30:
        message_text += f'\n\n*{_("Активні акаунти")}:*\n' + '\n'.join(active)
    else:
        with io.BytesIO() as file:
            file.name = 'active_accounts.txt'
            file.write('\n'.join(active).encode('utf-8'))
            input_file = types.input_file.BufferedInputFile(file.getvalue(), filename=file.name)
            message_files.append(types.InputMediaDocument(media=input_file, caption=_('Активні акаунти')))

    if len(blocked) <= 30:
        message_text += f'\n\n*{_("Заблоковані акаунти")}:*\n' + '\n'.join(blocked)
    else:
        with io.BytesIO() as file:
            file.name = 'blocked_accounts.txt'
            file.write('\n'.join(blocked).encode('utf-8'))
            input_file = types.input_file.BufferedInputFile(file.getvalue(), filename=file.name)
            message_files.append(types.InputMediaDocument(media=input_file, caption=_('Заблоковані акаунти')))

    await message.answer(message_text, parse_mode='markdown')

    if message_files:
        await message.bot(SendMediaGroup(chat_id=message.chat.id, media=message_files))
    await state.clear()
    await show_menu(message, state)
    usage.fb_acc_check += 1


@acc_check_router.message(CheckingAccounts.start_checking)
async def on_links_message(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    messages = state_data['messages']
    txt = state_data['txt']

    if message.document and not txt:
        with io.BytesIO() as file:
            await message.bot.download(message.document.file_id, file)
            raw_links = file.read().decode('utf-8')
        await state.update_data({'txt': raw_links})

    elif message.text and not txt:
        if len(messages) == 10:
            await message.answer(_('Забагато повідомлень, спробуйте менше'))
            await state.clear()
            await show_menu(message, state)

        messages.append(message.text)
        await state.update_data({'messages': messages})