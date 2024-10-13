import asyncio
import string
import secrets
import io

from faker import Faker
from aiogram import Router
from aiogram import types, F, filters
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from concurrent.futures import ThreadPoolExecutor

from .translations import handlers_variants, locales, countries, translations as ts
from .states import PasswordGen, NameGen, FanPageName, AddressGen, PhoneGen, QuoteGen, AllFanPageGen
from .callbacks import CountryPageCallback
from .quotes_storage import get_random_quotes
from functions import fan_page

class ForFarmers:
    def __init__(self, arbitrage_bot):
        self.router = Router()
        self.arbitrage_bot = arbitrage_bot
        self.bot = arbitrage_bot.bot

        self.gen_semaphore = asyncio.Semaphore(3)
        self.executor = ThreadPoolExecutor()

        self.register_handlers()

    def register_handlers(self):
        self.router.message(F.text.lower().in_(handlers_variants('for_farmers')))(self.farmers_menu)
        self.router.message(F.text.lower().in_(handlers_variants('fan_page_back')))(self.farmers_menu)

        self.router.message(F.text.lower().in_(handlers_variants('farm_password_gen')))(self.password_gen_start)
        self.router.callback_query(PasswordGen.tweaking)(self.password_gen_tweaking)
        self.router.message(PasswordGen.changing_chars)(self.password_input_value)
        self.router.message(PasswordGen.changing_amount)(self.password_input_value)

        self.router.message(F.text.lower().in_(handlers_variants('farm_name_gen')))(self.name_gen_start)
        self.router.callback_query(NameGen.selecting_gender)(self.name_gen_saving_gender)
        self.router.callback_query(CountryPageCallback.filter(F.action == 'page'), NameGen.selecting_country)(self.switch_country_page)
        self.router.callback_query(NameGen.selecting_country)(self.generate_names)

        self.router.message(F.text.lower().in_(handlers_variants('farm_fan_page_gen')))(self.fan_page)

        self.router.message(F.text.lower().in_(handlers_variants('fan_page_name')))(self.fan_page_name)
        self.router.message(FanPageName.entering_amount)(self.fan_page_name_gen)

        self.router.message(F.text.lower().in_(handlers_variants('fan_page_address')))(self.fan_page_address)
        self.router.callback_query(CountryPageCallback.filter(F.action == 'page'), AddressGen.selecting_country)(self.fan_page_change_locale_page)
        self.router.callback_query(AddressGen.selecting_country)(self.fan_page_address_amount)
        self.router.message(AddressGen.entering_amount)(self.fan_page_address_gen)

        self.router.message(F.text.lower().in_(handlers_variants('fan_page_phone')))(self.fan_page_phone)
        self.router.callback_query(CountryPageCallback.filter(F.action == 'page'), PhoneGen.selecting_country)(self.fan_page_change_locale_page)
        self.router.callback_query(PhoneGen.selecting_country)(self.phone_gen_amount)
        self.router.message(PhoneGen.entering_amount)(self.phone_gen)

        self.router.message(F.text.lower().in_(handlers_variants('fan_page_quote')))(self.fan_page_quotes)
        self.router.callback_query(CountryPageCallback.filter(F.action == 'page'), QuoteGen.selecting_country)(self.fan_page_change_locale_page)
        self.router.callback_query(QuoteGen.selecting_country)(self.quotes_amount)
        self.router.message(QuoteGen.entering_amount)(self.quotes_gen)

        self.router.message(F.text.lower().in_(handlers_variants('fan_page_all')))(self.fan_page_all)
        self.router.callback_query(CountryPageCallback.filter(F.action == 'page'), AllFanPageGen.selecting_country)(self.fan_page_change_locale_page)
        self.router.callback_query(AllFanPageGen.selecting_country)(self.fan_page_all_quantity)
        self.router.message(AllFanPageGen.entering_amount)(self.fan_page_all_gen)

    async def farmers_menu(self, message: types.Message, lang: str):
        menu_kb = ReplyKeyboardBuilder()
        menu_kb.button(text=ts[lang]['farm_password_gen'])
        menu_kb.button(text=ts[lang]['farm_name_gen'])
        menu_kb.button(text=ts[lang]['farm_fan_page_gen'])
        menu_kb.button(text=ts[lang]['to_menu'])
        menu_kb.adjust(3)

        await message.answer(ts[lang]['start_msg'], reply_markup=menu_kb.as_markup(resize_keyboard=True))

    def _password_keyboard(
            self,
            lang: str,
            n_chars: int = 10,
            special_chars: bool = True,
            letters: bool = True,
            uppercase: bool = True,
            send_as: str = 'Telegram',
            n_passwords: int = 10
    ):
        tweak_kb = InlineKeyboardBuilder()
        tweak_kb.button(text=f"{ts[lang]['n_chars']}: {n_chars}", callback_data='n_chars')
        tweak_kb.button(text=f"{ts[lang]['special_chars']}: {'🟢'if special_chars else '🔴'}", callback_data='special_chars')
        tweak_kb.button(text=f"{ts[lang]['letters']}: {'🟢'if letters else '🔴'}", callback_data='letters')
        tweak_kb.button(text=f"{ts[lang]['uppercase']}: {'🟢'if uppercase else '🔴'}", callback_data='uppercase')
        tweak_kb.button(text=f"{ts[lang]['send_as']}: {send_as}", callback_data='send_as')
        tweak_kb.button(text=f"{ts[lang]['n_passwords']}: {n_passwords}", callback_data='n_passwords')
        tweak_kb.button(text=f"{ts[lang]['generate_passwords']}", callback_data='generate_passwords')
        tweak_kb.adjust(1)

        return tweak_kb


    async def password_gen_start(self, message: types.Message, state: FSMContext, lang: str):
        data = await state.get_data()
        n_chars = data.get('n_chars', 10)
        special_chars = data.get('special_chars', True)
        letters = data.get('letters', True)
        uppercase = data.get('uppercase', True)
        send_as = data.get('send_as', 'Telegram')
        n_passwords = data.get('n_passwords', 10)

        tweak_kb = self._password_keyboard(lang, n_chars, special_chars, letters, uppercase, send_as, n_passwords)

        tweak_msg = await message.answer(ts[lang]['password_gen_tweaking'], reply_markup=tweak_kb.as_markup())
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

    async def password_gen_update(self, message: types.Message, state: FSMContext, lang: str):
        data = await state.get_data()
        n_chars = data.get('n_chars', 10)
        special_chars = data.get('special_chars', True)
        letters = data.get('letters', True)
        uppercase = data.get('uppercase', True)
        send_as = data.get('send_as', 'Telegram')
        n_passwords = data.get('n_passwords', 10)
        this_message_id = data.get('this_message_id')

        tweak_kb = self._password_keyboard(lang, n_chars, special_chars, letters, uppercase, send_as, n_passwords)

        try:
            await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=this_message_id, reply_markup=tweak_kb.as_markup())
        except Exception as e:
            print(e)

        await state.set_state(PasswordGen.tweaking)

    async def password_gen_tweaking(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        data = await state.get_data()

        if callback.data == 'n_chars':
            await callback.message.answer(ts[lang]['password_enter_value'].format(1, 50))
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
            await callback.message.answer(ts[lang]['password_enter_value'].format(1, 500))
            await state.set_state(PasswordGen.changing_amount)
            await callback.answer()
            return
        elif callback.data == 'generate_passwords':
            await callback.message.answer(ts[lang]['password_generating'])
            await callback.answer()
            await self.generate_passwords(callback, state, lang)
            return

        await state.update_data(data)
        await callback.answer()
        await self.password_gen_update(callback.message, state, lang)

    async def password_input_value(self, message: types.Message, state: FSMContext, lang: str):
        try:
            value = int(message.text)
        except ValueError:
            await message.answer(ts[lang]['password_invalid_value'])
            return

        state_name = await state.get_state()
        if state_name == PasswordGen.changing_chars:
            if value < 1 or value > 50:
                await message.answer(ts[lang]['password_enter_value'].format(1, 50))
                return

            await state.update_data(n_chars=value)
        elif state_name == PasswordGen.changing_amount:
            if value < 1 or value > 500:
                await message.answer(ts[lang]['password_enter_value'].format(1, 500))
                return

            await state.update_data(n_passwords=value)

        data = await state.get_data()
        await message.bot.delete_message(chat_id=message.chat.id, message_id=data['this_message_id'])
        await self.password_gen_start(message, state, lang)

    async def generate_passwords(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        data = await state.get_data()
        n_chars = data.get('n_chars', 10)
        special_chars = data.get('special_chars', True)
        letters = data.get('letters', True)
        uppercase = data.get('uppercase', True)
        send_as = data.get('send_as', 'Telegram')
        n_passwords = data.get('n_passwords', 10)

        async with self.gen_semaphore:
            loop = asyncio.get_event_loop()
            passwords = await loop.run_in_executor(self.executor, fan_page.password_gen, n_chars, special_chars, letters, uppercase, n_passwords)

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
        await self.farmers_menu(callback.message, lang)

    async def name_gen_start(self, message: types.Message, state: FSMContext, lang: str):
        gender_kb = InlineKeyboardBuilder()
        gender_kb.button(text=ts[lang]['male'], callback_data='male')
        gender_kb.button(text=ts[lang]['female'], callback_data='female')
        gender_kb.button(text=ts[lang]['both'], callback_data='both')
        gender_kb.adjust(1)

        message = await message.answer(ts[lang]['name_gen_sel_gender'], reply_markup=gender_kb.as_markup())
        await state.set_state(NameGen.selecting_gender)
        await state.update_data(this_message_id=message.message_id)

    def _countries_kb(self, page: int, total_pages: int, lang: str):
        kb = InlineKeyboardBuilder()

        locale_items = list(countries[lang].items())
        locale_page_items = locale_items[page * 14:page * 14 + 14]
        locale_page = dict(locale_page_items)

        for code, name in locale_page.items():
            kb.button(text=name, callback_data=code)
        kb.adjust(2)

        nav_row = []
        if page > 0:
            nav_row.append(types.InlineKeyboardButton(text='⬅️', callback_data=CountryPageCallback(direction='prev', action='page').pack()))
        nav_row.append(types.InlineKeyboardButton(text=ts[lang]['random_country'], callback_data='random'))
        if page < total_pages:
            nav_row.append(types.InlineKeyboardButton(text='➡️', callback_data=CountryPageCallback(direction='next', action='page').pack()))

        kb.row(*nav_row)

        return kb
    async def name_gen_saving_gender(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        gender = callback.data
        country_pages = len(locales) // 14

        data = await state.get_data()
        current_page = data.get('country_page', 0)

        await state.update_data(gender=gender, country_page=current_page)

        kb = self._countries_kb(current_page, country_pages, lang)
        await callback.bot.edit_message_text(chat_id=callback.message.chat.id,
                                             message_id=data['this_message_id'],
                                             text=ts[lang]['name_gen_sel_country'],
                                             reply_markup=kb.as_markup())

        await callback.answer()

        await state.set_state(NameGen.selecting_country)

    async def switch_country_page(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        data = await state.get_data()
        current_page = data.get('country_page', 0)
        country_pages = len(locales) // 14

        callback_data = CountryPageCallback.unpack(callback.data)
        await callback.answer()

        if callback_data.direction == 'next':
            current_page += 1
        else:
            current_page -= 1

        kb = self._countries_kb(current_page, country_pages, lang)
        await callback.bot.edit_message_reply_markup(chat_id=callback.message.chat.id,
                                                     message_id=data['this_message_id'],
                                                     reply_markup=kb.as_markup())
        await state.update_data(country_page=current_page)

    async def generate_names(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        data = await state.get_data()
        gender = data['gender']
        locale = callback.data
        if locale == 'random':
            locale = secrets.choice(list(locales.keys()))

        await callback.answer()

        async with self.gen_semaphore:
            loop = asyncio.get_event_loop()
            names = await loop.run_in_executor(self.executor, fan_page.generate_names_task, gender, locale, 40)

        await callback.message.answer(''.join(names), parse_mode='Markdown')
        await state.clear()
        await self.farmers_menu(callback.message, lang)

    async def fan_page(self, message: types.Message, state: FSMContext, lang: str):
        fan_page_kb = ReplyKeyboardBuilder()
        fan_page_kb.row(types.KeyboardButton(text=ts[lang]['fan_page_name']),
                        types.KeyboardButton(text=ts[lang]['fan_page_address']),
                        types.KeyboardButton(text=ts[lang]['fan_page_phone']))
        fan_page_kb.row(types.KeyboardButton(text=ts[lang]['fan_page_quote']),
                        types.KeyboardButton(text=ts[lang]['fan_page_all']))
        fan_page_kb.row(types.KeyboardButton(text=ts[lang]['fan_page_back']))


        await message.answer(ts[lang]['fan_page_select_option'], reply_markup=fan_page_kb.as_markup(resize_keyboard=True))

    async def fan_page_name(self, message: types.Message, state: FSMContext, lang: str):
        await message.answer(ts[lang]['fan_page_ask_num_names'])
        await state.set_state(FanPageName.entering_amount)

    async def fan_page_name_gen(self, message: types.Message, state: FSMContext, lang: str):
        try:
            amount = int(message.text)
            if amount < 1 or amount > 100:
                raise ValueError
        except ValueError:
            await message.answer(ts[lang]['fan_page_invalid_num'].format(1, 100))
            return

        async with self.gen_semaphore:
            loop = asyncio.get_event_loop()
            names = await loop.run_in_executor(self.executor, fan_page.generate_fan_page_names, amount)

        await self._send_message_and_txt(message, '\n'.join(names), 'fan_page_names.txt')
        await state.clear()

    async def fan_page_sel_locale(self, message: types.Message, state: FSMContext, lang: str):
        country_pages = len(locales) // 14
        data = await state.get_data()
        current_page = data.get('country_page', 0)

        kb = self._countries_kb(current_page, country_pages, lang)

        message = await message.answer(ts[lang]['name_gen_sel_country'], reply_markup=kb.as_markup())
        await state.update_data(locale_message_id=message.message_id, country_page=current_page)

    async def fan_page_change_locale_page(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        data = await state.get_data()
        current_page = data.get('country_page', 0)
        country_pages = len(locales) // 14

        callback_data = CountryPageCallback.unpack(callback.data)
        await callback.answer()

        if callback_data.direction == 'next':
            current_page += 1
        else:
            current_page -= 1

        kb = self._countries_kb(current_page, country_pages, lang)
        await callback.bot.edit_message_reply_markup(chat_id=callback.message.chat.id,
                                                     message_id=data['locale_message_id'],
                                                     reply_markup=kb.as_markup())
        await state.update_data(country_page=current_page)

    async def fan_page_address(self, message: types.Message, state: FSMContext, lang: str):
        await state.set_state(AddressGen.selecting_country)
        await self.fan_page_sel_locale(message, state, lang)

    async def fan_page_address_amount(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        await callback.answer()
        locale = callback.data
        if locale == 'random':
            locale = secrets.choice(list(locales.keys()))

        await state.update_data(locale=locale)

        data = await state.get_data()
        locale_message_id = data['locale_message_id']
        await callback.bot.edit_message_text(chat_id=callback.message.chat.id, message_id=locale_message_id, text=ts[lang]['fan_page_ask_num_addresses'])
        await state.set_state(AddressGen.entering_amount)

    async def fan_page_address_gen(self, message: types.Message, state: FSMContext, lang: str):
        try:
            amount = int(message.text)
            if amount < 1 or amount > 50:
                raise ValueError
        except ValueError:
            await message.answer(ts[lang]['fan_page_invalid_num'].format(1, 50))
            return

        data = await state.get_data()
        locale = data['locale']

        async with self.gen_semaphore:
            try:
                addresses = await fan_page.generate_addresses(locale, amount)
                await self._send_message_and_txt(message, '\n'.join(addresses), f'{locale} addresses.txt')
            except AttributeError as e:
                await message.answer(ts[lang]['farm_gen_error'])
            finally:
                await state.clear()


    async def fan_page_phone(self, message: types.Message, state: FSMContext, lang: str):
        await state.set_state(PhoneGen.selecting_country)
        await self.fan_page_sel_locale(message, state, lang)

    async def phone_gen_amount(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        await callback.answer()
        locale = callback.data
        if locale == 'random':
            locale = secrets.choice(list(locales.keys()))

        await state.update_data(locale=locale)

        data = await state.get_data()
        locale_message_id = data['locale_message_id']
        await callback.bot.edit_message_text(chat_id=callback.message.chat.id, message_id=locale_message_id, text=ts[lang]['fan_page_ask_num_phones'])
        await state.set_state(PhoneGen.entering_amount)

    async def phone_gen(self, message: types.Message, state: FSMContext, lang: str):
        try:
            amount = int(message.text)
            if amount < 1 or amount > 100:
                raise ValueError
        except ValueError:
            await message.answer(ts[lang]['fan_page_invalid_num'].format(1, 100))
            return

        data = await state.get_data()
        locale = data['locale']

        async with self.gen_semaphore:
            loop = asyncio.get_event_loop()
            phones = await loop.run_in_executor(self.executor, fan_page.generate_phones, locale, amount)

        await self._send_message_and_txt(message, '\n'.join(phones), f'{locale} phones.txt')
        await state.clear()


    async def fan_page_quotes(self, message: types.Message, state: FSMContext, lang: str):
        await state.set_state(QuoteGen.selecting_country)
        await self.fan_page_sel_locale(message, state, lang)

    async def quotes_amount(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        await callback.answer()
        locale = callback.data
        if locale == 'random':
            locale = secrets.choice(list(locales.keys()))

        await state.update_data(locale=locale)

        data = await state.get_data()
        locale_message_id = data['locale_message_id']
        await callback.bot.edit_message_text(chat_id=callback.message.chat.id, message_id=locale_message_id, text=ts[lang]['fan_page_ask_num_quotes'])
        await state.set_state(QuoteGen.entering_amount)

    async def quotes_gen(self, message: types.Message, state: FSMContext, lang: str):
        try:
            amount = int(message.text)
            if amount < 1 or amount > 50:
                raise ValueError
        except ValueError:
            await message.answer(ts[lang]['fan_page_invalid_num'].format(1, 50))
            return

        data = await state.get_data()
        locale = data['locale']

        async with self.gen_semaphore:
            quotes = await get_random_quotes(locale, amount)

        await self._send_message_and_txt(message, '\n'.join(quotes), f'{locale} quotes.txt')
        await state.clear()

    async def fan_page_all(self, message: types.Message, state: FSMContext, lang: str):
        await state.set_state(AllFanPageGen.selecting_country)
        await self.fan_page_sel_locale(message, state, lang)

    async def fan_page_all_quantity(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        await callback.answer()
        locale = callback.data
        if locale == 'random':
            locale = secrets.choice(list(locales.keys()))

        await state.update_data(locale=locale)

        data = await state.get_data()
        locale_message_id = data['locale_message_id']
        await callback.bot.edit_message_text(chat_id=callback.message.chat.id, message_id=locale_message_id, text=ts[lang]['fan_page_ask_num_all'])
        await state.set_state(AllFanPageGen.entering_amount)

    async def fan_page_all_gen(self, message: types.Message, state: FSMContext, lang: str):
        try:
            amount = int(message.text)
            if amount < 1 or amount > 50:
                raise ValueError
        except ValueError:
            await message.answer(ts[lang]['fan_page_invalid_num'].format(1, 10))
            return

        data = await state.get_data()
        locale = data['locale']

        async with self.gen_semaphore:
            loop = asyncio.get_event_loop()
            names = loop.run_in_executor(self.executor, fan_page.generate_fan_page_names, amount)
            addresses = fan_page.generate_addresses(locale, amount)
            phones = loop.run_in_executor(self.executor, fan_page.generate_phones, locale, amount)
            quotes = get_random_quotes(locale, amount)

        names = await names
        addresses = await addresses
        phones = await phones
        quotes = await quotes

        text = ''
        for i in range(amount):
            text += f"{i+1}. {ts[lang]['fan_page_all_answer'].format(names[i], addresses[i], phones[i], quotes[i])}\n\n"

        await self._send_message_and_txt(message, text, 'fan_page_all.txt')
        await state.clear()

    async def _send_message_and_txt(self, message: types.Message, text: str, filename: str):
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

