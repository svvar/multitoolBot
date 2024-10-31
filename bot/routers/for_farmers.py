import asyncio
import secrets
import io

from aiogram import Router
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import I18n, gettext as _, lazy_gettext as __
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from concurrent.futures import ThreadPoolExecutor

from bot.core.locale_helper import locales, countries
from bot.core.states import PasswordGen, NameGen, FanPageName, AddressGen, PhoneGen, QuoteGen, AllFanPageGen
from bot.core.callbacks import CountryPageCallback
from bot.core.storage.quotes_storage import get_random_quotes
from bot.functions.fan_page import generate_names_task, generate_addresses, generate_phones, password_gen


farmers_router = Router()
gen_semaphore = asyncio.Semaphore(3)
executor = ThreadPoolExecutor()


@farmers_router.message(F.text == __('🚀 Фармерам'))
@farmers_router.message(F.text == __('↩️ Назад'))
async def farmers_menu(message: types.Message):
    menu_kb = ReplyKeyboardBuilder()
    menu_kb.button(text=_('🔐 Генератор паролів'))
    menu_kb.button(text=_('👨 Генератор імен'))
    menu_kb.button(text=_('⚡️ Генератор fan-page'))
    menu_kb.button(text=_('🏠 В меню'))
    menu_kb.adjust(3)

    await message.answer(_('Виберіть дію з меню:'), reply_markup=menu_kb.as_markup(resize_keyboard=True))

def _password_keyboard(
        n_chars: int = 10,
        special_chars: bool = True,
        letters: bool = True,
        uppercase: bool = True,
        send_as: str = 'Telegram',
        n_passwords: int = 10
):
    tweak_kb = InlineKeyboardBuilder()
    tweak_kb.button(text=f"{_('📏 Кількість символів')}: {n_chars}", callback_data='n_chars')
    tweak_kb.button(text=f"{_('⭐ Спеціальні символи')}: {'🟢' if special_chars else '🔴'}", callback_data='special_chars')
    tweak_kb.button(text=f"{_('🔤 Малі літери')}: {'🟢' if letters else '🔴'}", callback_data='letters')
    tweak_kb.button(text=f"{_('🔠 Великі літери')}: {'🟢' if uppercase else '🔴'}", callback_data='uppercase')
    tweak_kb.button(text=f"{_('📤 Спосіб відправки')}: {send_as}", callback_data='send_as')
    tweak_kb.button(text=f"{_('🔑 Кількість паролів')}: {n_passwords}", callback_data='n_passwords')
    tweak_kb.button(text=f"{_('⚙️ Згенерувати')}", callback_data='generate_passwords')
    tweak_kb.adjust(1)

    return tweak_kb


@farmers_router.message(F.text == __('🔐 Генератор паролів'))
async def password_gen_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    n_chars = data.get('n_chars', 10)
    special_chars = data.get('special_chars', True)
    letters = data.get('letters', True)
    uppercase = data.get('uppercase', True)
    send_as = data.get('send_as', 'Telegram')
    n_passwords = data.get('n_passwords', 10)

    tweak_kb = _password_keyboard(n_chars, special_chars, letters, uppercase, send_as, n_passwords)

    tweak_msg = await message.answer(_('Налаштуйте кнопками нижче'), reply_markup=tweak_kb.as_markup())
    await state.set_state(PasswordGen.tweaking)
    await state.update_data({
        'n_chars': n_chars,
        'special_chars': special_chars,
        'letters': letters,
        'uppercase': uppercase,
        'send_as': send_as,
        'n_passwords': n_passwords,
        'this_message_id': tweak_msg.message_id
    })


async def password_gen_update(message: types.Message, state: FSMContext):
    data = await state.get_data()
    n_chars = data.get('n_chars', 10)
    special_chars = data.get('special_chars', True)
    letters = data.get('letters', True)
    uppercase = data.get('uppercase', True)
    send_as = data.get('send_as', 'Telegram')
    n_passwords = data.get('n_passwords', 10)
    this_message_id = data.get('this_message_id')

    tweak_kb = _password_keyboard(n_chars, special_chars, letters, uppercase, send_as, n_passwords)

    try:
        await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=this_message_id,
                                                    reply_markup=tweak_kb.as_markup())
    except Exception as e:
        print(e)

    await state.set_state(PasswordGen.tweaking)


@farmers_router.callback_query(PasswordGen.tweaking)
async def password_gen_tweaking(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if callback.data == 'n_chars':
        await callback.message.answer(_('Введіть значення від {} до {}:').format(1, 50))
        await state.set_state(PasswordGen.changing_chars)
        await callback.answer()
        return
    elif callback.data == 'special_chars':
        data['special_chars'] = not data['special_chars']
    elif callback.data == 'letters':
        data['letters'] = not data['letters']
    elif callback.data == 'uppercase':
        data['uppercase'] = not data['uppercase']
    elif callback.data == 'send_as':
        data['send_as'] = 'TXT' if data['send_as'] == 'Telegram' else 'Telegram'
    elif callback.data == 'n_passwords':
        await callback.message.answer(_('Введіть значення від {} до {}:').format(1, 500))
        await state.set_state(PasswordGen.changing_amount)
        await callback.answer()
        return
    elif callback.data == 'generate_passwords':
        await callback.message.answer(_('⏳ Генерація...'))
        await callback.answer()
        await generate_passwords(callback, state)
        return

    await state.update_data(data)
    await callback.answer()
    await password_gen_update(callback.message, state)


@farmers_router.message(PasswordGen.changing_chars)
@farmers_router.message(PasswordGen.changing_amount)
async def password_input_value(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
    except ValueError:
        await message.answer(_('Некоректне значення, введіть ще раз'))
        return

    state_name = await state.get_state()
    if state_name == PasswordGen.changing_chars:
        if value < 1 or value > 50:
            await message.answer(_('Введіть значення від {} до {}:').format(1, 50))
            return

        await state.update_data(n_chars=value)
    elif state_name == PasswordGen.changing_amount:
        if value < 1 or value > 500:
            await message.answer(_('Введіть значення від {} до {}:').format(1, 500))
            return

        await state.update_data(n_passwords=value)

    data = await state.get_data()
    await message.bot.delete_message(chat_id=message.chat.id, message_id=data['this_message_id'])
    await password_gen_start(message, state)



async def generate_passwords(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    n_chars = data.get('n_chars', 10)
    special_chars = data.get('special_chars', True)
    letters = data.get('letters', True)
    uppercase = data.get('uppercase', True)
    send_as = data.get('send_as', 'Telegram')
    n_passwords = data.get('n_passwords', 10)

    async with gen_semaphore:
        loop = asyncio.get_event_loop()
        passwords = await loop.run_in_executor(executor, password_gen, n_chars, special_chars, letters,
                                               uppercase, n_passwords)

    if send_as == 'Telegram':
        await callback.message.answer('\n'.join(passwords))
    else:
        buffer = io.BytesIO()
        buffer.name = 'passwords.txt'
        buffer.write('\n'.join(passwords).encode())
        buffer.seek(0)

        input_file = types.BufferedInputFile(buffer.getvalue(), filename='passwords.txt')
        await callback.message.answer_document(input_file)

    await state.clear()
    await farmers_menu(callback.message)


@farmers_router.message(F.text == __('👨 Генератор імен'))
async def name_gen_start(message: types.Message, state: FSMContext):
    gender_kb = InlineKeyboardBuilder()
    gender_kb.button(text=_('🕺 Чоловіча'), callback_data='male')
    gender_kb.button(text=_('💃 Жіноча'), callback_data='female')
    gender_kb.button(text=_('👫 Обидві'), callback_data='both')
    gender_kb.adjust(1)

    message = await message.answer(_('Виберіть стать:'), reply_markup=gender_kb.as_markup())
    await state.set_state(NameGen.selecting_gender)
    await state.update_data(this_message_id=message.message_id)


def _countries_kb(page: int, total_pages: int, locale: str):
    kb = InlineKeyboardBuilder()

    locale_items = list(countries[locale].items())
    locale_page_items = locale_items[page * 14:page * 14 + 14]
    locale_page = dict(locale_page_items)

    for code, name in locale_page.items():
        kb.button(text=name, callback_data=code)
    kb.adjust(2)

    nav_row = []
    if page > 0:
        nav_row.append(types.InlineKeyboardButton(text='⬅️', callback_data=CountryPageCallback(direction='prev',
                                                                                               action='page').pack()))
    nav_row.append(types.InlineKeyboardButton(text=_('🎲 Випадкова'), callback_data='random'))
    if page < total_pages:
        nav_row.append(types.InlineKeyboardButton(text='➡️', callback_data=CountryPageCallback(direction='next',
                                                                                               action='page').pack()))

    kb.row(*nav_row)

    return kb


@farmers_router.callback_query(NameGen.selecting_gender)
async def name_gen_saving_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data
    country_pages = len(locales) // 14

    data = await state.get_data()
    current_page = data.get('country_page', 0)

    await state.update_data(gender=gender, country_page=current_page)
    locale = I18n.get_current()
    kb = _countries_kb(current_page, country_pages, locale.current_locale)
    await callback.bot.edit_message_text(chat_id=callback.message.chat.id,
                                         message_id=data['this_message_id'],
                                         text=_('Виберіть країну:'),
                                         reply_markup=kb.as_markup())

    await callback.answer()

    await state.set_state(NameGen.selecting_country)


@farmers_router.callback_query(CountryPageCallback.filter(F.action == 'page'))
# @farmers_router.callback_query(NameGen.selecting_country, CountryPageCallback.filter(F.action == 'page'))
async def switch_country_page(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get('country_page', 0)
    country_pages = len(locales) // 14

    callback_data = CountryPageCallback.unpack(callback.data)
    await callback.answer()

    if callback_data.direction == 'next':
        current_page += 1
    else:
        current_page -= 1

    locale = I18n.get_current()
    kb = _countries_kb(current_page, country_pages, locale.current_locale)
    await callback.bot.edit_message_reply_markup(chat_id=callback.message.chat.id,
                                                 message_id=data['this_message_id'],
                                                 reply_markup=kb.as_markup())
    await state.update_data(country_page=current_page)


@farmers_router.callback_query(NameGen.selecting_country)
async def generate_names(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    gender = data['gender']
    locale = callback.data
    if locale == 'random':
        locale = secrets.choice(list(locales.keys()))

    await callback.answer()

    async with gen_semaphore:
        loop = asyncio.get_event_loop()
        names = await loop.run_in_executor(executor, generate_names_task, gender, locale, 40)

    await callback.message.answer(''.join(names), parse_mode='Markdown')
    await state.clear()
    await farmers_menu(callback.message)


@farmers_router.message(F.text == __('⚡️ Генератор fan-page'))
async def fan_page(message: types.Message, state: FSMContext):
    fan_page_kb = ReplyKeyboardBuilder()
    fan_page_kb.row(types.KeyboardButton(text=_('🏷️ Назва')),
                    types.KeyboardButton(text=_('📍 Адреса')),
                    types.KeyboardButton(text=_('📞 Телефон')))
    fan_page_kb.row(types.KeyboardButton(text=_('💬 Цитата')),
                    types.KeyboardButton(text=_('🌐 Все разом')))
    fan_page_kb.row(types.KeyboardButton(text=_('↩️ Назад')))

    await message.answer(_('Виберіть пункт меню:'), reply_markup=fan_page_kb.as_markup(resize_keyboard=True))


@farmers_router.message(F.text == __('🏷️ Назва'))
async def fan_page_name(message: types.Message, state: FSMContext):
    await message.answer(_('Введіть кількість назв:'))
    await state.set_state(FanPageName.entering_amount)


@farmers_router.message(FanPageName.entering_amount)
async def fan_page_name_gen(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount < 1 or amount > 100:
            raise ValueError
    except ValueError:
        await message.answer(_('Введіть число від {} до {}').format(1, 100))
        return

    async with gen_semaphore:
        loop = asyncio.get_event_loop()
        names = await loop.run_in_executor(executor, fan_page.generate_fan_page_names, amount)

    await _send_message_and_txt(message, '\n'.join(names), 'fan_page_names.txt')
    await state.clear()


async def fan_page_sel_locale(message: types.Message, state: FSMContext):
    country_pages = len(locales) // 14
    data = await state.get_data()
    current_page = data.get('country_page', 0)

    locale = I18n.get_current()
    kb = _countries_kb(current_page, country_pages, locale.current_locale)

    message = await message.answer(_('Виберіть країну:'), reply_markup=kb.as_markup())
    await state.update_data(locale_message_id=message.message_id, country_page=current_page)


@farmers_router.message(F.text == __('📍 Адреса'))
async def fan_page_address(message: types.Message, state: FSMContext):
    await state.set_state(AddressGen.selecting_country)
    await fan_page_sel_locale(message, state)


@farmers_router.callback_query(AddressGen.selecting_country)
async def fan_page_address_amount(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    locale = callback.data
    if locale == 'random':
        locale = secrets.choice(list(locales.keys()))

    await state.update_data(locale=locale)

    data = await state.get_data()
    locale_message_id = data['locale_message_id']
    await callback.bot.edit_message_text(chat_id=callback.message.chat.id, message_id=locale_message_id,
                                         text=_('Введіть кількість адрес:'))
    await state.set_state(AddressGen.entering_amount)


@farmers_router.message(AddressGen.entering_amount)
async def fan_page_address_gen(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount < 1 or amount > 50:
            raise ValueError
    except ValueError:
        await message.answer(_('Введіть число від {} до {}').format(1, 50))
        return

    data = await state.get_data()
    locale = data['locale']

    async with gen_semaphore:
        try:
            addresses = await generate_addresses(locale, amount)
            await _send_message_and_txt(message, '\n'.join(addresses), f'{locale} addresses.txt')
        except AttributeError as e:
            await message.answer(_('Помилка генерації, спробуйте пізніше'))
        finally:
            await state.clear()


@farmers_router.message(F.text == __('📞 Телефон'))
async def fan_page_phone(message: types.Message, state: FSMContext):
    await state.set_state(PhoneGen.selecting_country)
    await fan_page_sel_locale(message, state)


@farmers_router.callback_query(PhoneGen.selecting_country)
async def phone_gen_amount(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    locale = callback.data
    if locale == 'random':
        locale = secrets.choice(list(locales.keys()))

    await state.update_data(locale=locale)

    data = await state.get_data()
    locale_message_id = data['locale_message_id']
    await callback.bot.edit_message_text(chat_id=callback.message.chat.id, message_id=locale_message_id,
                                         text=_('Введіть кількість номерів телефону:'))
    await state.set_state(PhoneGen.entering_amount)


@farmers_router.message(PhoneGen.entering_amount)
async def phone_gen(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount < 1 or amount > 100:
            raise ValueError
    except ValueError:
        await message.answer(_('Введіть число від {} до {}').format(1, 100))
        return

    data = await state.get_data()
    locale = data['locale']

    async with gen_semaphore:
        loop = asyncio.get_event_loop()
        phones = await loop.run_in_executor(executor, generate_phones, locale, amount)

    await _send_message_and_txt(message, '\n'.join(phones), f'{locale} phones.txt')
    await state.clear()


@farmers_router.message(F.text == __('💬 Цитата'))
async def fan_page_quotes(message: types.Message, state: FSMContext):
    await state.set_state(QuoteGen.selecting_country)
    await fan_page_sel_locale(message, state)


@farmers_router.callback_query(QuoteGen.selecting_country)
async def quotes_amount(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    locale = callback.data
    if locale == 'random':
        locale = secrets.choice(list(locales.keys()))

    await state.update_data(locale=locale)

    data = await state.get_data()
    locale_message_id = data['locale_message_id']
    await callback.bot.edit_message_text(chat_id=callback.message.chat.id, message_id=locale_message_id,
                                         text=_('Введіть кількість цитат:'))
    await state.set_state(QuoteGen.entering_amount)


@farmers_router.message(QuoteGen.entering_amount)
async def quotes_gen(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount < 1 or amount > 50:
            raise ValueError
    except ValueError:
        await message.answer(_('Введіть число від {} до {}').format(1, 50))
        return

    data = await state.get_data()
    locale = data['locale']

    async with gen_semaphore:
        quotes = await get_random_quotes(locale, amount)

    await _send_message_and_txt(message, '\n'.join(quotes), f'{locale} quotes.txt')
    await state.clear()


@farmers_router.message(F.text == __('🌐 Все разом'))
async def fan_page_all(message: types.Message, state: FSMContext):
    await state.set_state(AllFanPageGen.selecting_country)
    await fan_page_sel_locale(message, state)


@farmers_router.callback_query(AllFanPageGen.selecting_country)
async def fan_page_all_quantity(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    locale = callback.data
    if locale == 'random':
        locale = secrets.choice(list(locales.keys()))

    await state.update_data(locale=locale)

    data = await state.get_data()
    locale_message_id = data['locale_message_id']
    await callback.bot.edit_message_text(chat_id=callback.message.chat.id, message_id=locale_message_id,
                                         text=_('Введіть кількість fan page:'))
    await state.set_state(AllFanPageGen.entering_amount)


@farmers_router.message(AllFanPageGen.entering_amount)
async def fan_page_all_gen(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount < 1 or amount > 50:
            raise ValueError
    except ValueError:
        await message.answer(_('Введіть число від {} до {}').format(1, 10))
        return

    data = await state.get_data()
    locale = data['locale']

    async with gen_semaphore:
        loop = asyncio.get_event_loop()
        names = loop.run_in_executor(executor, fan_page.generate_fan_page_names, amount)
        addresses = generate_addresses(locale, amount)
        phones = loop.run_in_executor(executor, generate_phones, locale, amount)
        quotes = get_random_quotes(locale, amount)

    names = await names
    addresses = await addresses
    phones = await phones
    quotes = await quotes

    text = ''
    for i in range(amount):
        formatted_part = _('Назва fan page: {}\nАдреса: {}\nНомер телефону: {}\nЦитата: {}').format(names[i], addresses[i], phones[i], quotes[i])
        text += f"{i + 1}. {formatted_part}\n\n"

    await _send_message_and_txt(message, text, 'fan_page_all.txt')
    await state.clear()


async def _send_message_and_txt(message: types.Message, text: str, filename: str):
    buffer = io.BytesIO()
    buffer.name = filename
    buffer.write(text.encode())
    buffer.seek(0)

    input_file = types.BufferedInputFile(buffer.getvalue(), filename=buffer.name)

    if len(text) > 4096:
        await message.answer_document(input_file)
    else:
        await message.answer(text)
        await message.answer_document(input_file)
