import io

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendMediaGroup
from aiogram.types import Message, InputMediaDocument, input_file as types_input_file
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.core.states import TransferFanPage
from bot.core.storage.main_storage import get_user_balance
from bot.functions import fb_account_checking
from bot.main_menu import show_menu
from bot.routers.fb_acc_check import check_semaphore
from bot.core.storage.main_storage import get_user_balance

transfer_fp = Router()

@transfer_fp.message(F.text == __("➡️ Передати Fan Page"))
async def check_account_blocked(message: Message, state: FSMContext):
    kb = ReplyKeyboardBuilder()
    kb.button(text=_('Почати перевірку'))
    kb.button(text=_('🏠 В меню')).button(text=_('🔧🐞 Повідомити про помилку')).adjust(1)
    kb.adjust(1)

    await message.answer(_("✍️ Для передачі Fan Page надішліть, будь ласка, список посилань на свої облікові записи Facebook (кожне посилання з нового рядка) повідомленням/ями або .txt-файлом."),
                         reply_markup=kb.as_markup(resize_keyboard=True))
    await state.set_state(TransferFanPage.start_checking)
    await state.update_data({'messages': [], 'txt': None})


@transfer_fp.message(TransferFanPage.start_checking, F.text == __('Почати перевірку'))
async def check_links(message: Message, state: FSMContext):

    await message.answer(_("⏳ Перевірка облікових записів на бан, будь ласка, зачекайте ..."))

    state_data = await state.get_data()
    messages = '\n'.join(state_data['messages'])
    txt = state_data['txt']

    raw_links = txt if txt else messages

    links = fb_account_checking.extract_links(raw_links)

    async with check_semaphore:
        active, blocked, errors = await fb_account_checking.check_urls(links)

    await state.update_data(account_number=len(active))

    message_text = _("""*
Количество аккаунтов: {}
🔴 Заблокованих аккаунтiв: {}
🟢 Активних аккаунтiв: {}
    *""").format(len(active)+len(blocked), len(blocked), len(active))
    message_files = []

    if len(active) <= 30:
        message_text += f'\n\n*{_("Активні акаунти")}:*\n' + '\n'.join(active)
    else:
        with io.BytesIO() as file:
            file.name = 'active_accounts.txt'
            file.write('\n'.join(active).encode('utf-8'))
            input_file = types_input_file.BufferedInputFile(file.getvalue(), filename=file.name)
            message_files.append(InputMediaDocument(media=input_file, caption=_('Активні акаунти')))

    if len(blocked) <= 30:
        message_text += f'\n\n*{_("Заблоковані акаунти")}:*\n' + '\n'.join(blocked)
    else:
        with io.BytesIO() as file:
            file.name = 'blocked_accounts.txt'
            file.write('\n'.join(blocked).encode('utf-8'))
            input_file = types_input_file.BufferedInputFile(file.getvalue(), filename=file.name)
            message_files.append(InputMediaDocument(media=input_file, caption=_('Заблоковані акаунти')))

    await message.answer(message_text, parse_mode='markdown')

    if message_files:
        await message.bot(SendMediaGroup(chat_id=message.chat.id, media=message_files))

    if len(active) > 0:
        await state.set_state(TransferFanPage.fp_for_every_account)
        await message.answer(_("✍️ Введіть кількість Fan Page для передачі на кожний обліковий запис Вартість Fan Page - 0.15$."))
    else:
        await show_menu(message, state)


@transfer_fp.message(TransferFanPage.start_checking)
async def on_links_message(message: Message, state: FSMContext):
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

@transfer_fp.message(TransferFanPage.fp_for_every_account)
async def fp_for_every_account(message: Message, state: FSMContext):

    await state.update_data(fp_for_every_account=message.text)
    user_request = await state.get_data()

    balance = await get_user_balance(message.from_user.id)
    needed_amount = int(user_request['fp_for_every_account'])*int(user_request['account_number'])*0.15

    if balance >= needed_amount:

        await message.answer(_("Запит на передачу прийнято!"))
        await show_menu(message, state)

    else:

        lacking_amount = needed_amount - balance

        await message.answer(_("⚠️ Недостатньо коштів на балансі. Необхідна сума: {} $, сума на балансі: {} $, брак коштів: {} $.").format(needed_amount, balance, lacking_amount))
        await message.answer(_("✍️ Для поповнення балансу напишіть сапорту @mustage_support (можлива оплата в USDT): Привіт, хочу поповнити баланс у роботі @mustage_service_bot на {сумма_поповнення} $."))
        await show_menu(message, state)