from aiogram import Bot, Dispatcher, types, F, filters
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup
from aiogram.methods import SendMediaGroup

from functions import account_checking

import io

from .states import *

class ArbitrageBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()

        # self.user_storage = user_storage

        self.register_handlers()

    def register_handlers(self):
        self.dp.message(filters.command.Command('start'))(self.start_msg)
        self.dp.message(F.text.lower() == 'перевірити акаунти на блокування')(self.check_account_blocked)
        self.dp.message(CheckingAccounts.start_checking)(self.on_account_list)
        pass


    async def start_msg(self, message: types.Message):
        # if not await self.user_storage.check_user(message.from_user.id):
        #     # TODO add user to db
        #     await self.user_storage.save_user(message.from_user.id)

        kb = ReplyKeyboardBuilder()
        kb.button(text='Перевірити акаунти на блокування')

        await message.answer('Привіт, я бот для арбітражу', reply_markup=kb.as_markup())


    async def check_account_blocked(self, message: types.Message, state: FSMContext):
        await message.answer('Відправте список посилань на акаунти або txt файл з посиланнями')
        await state.set_state(CheckingAccounts.start_checking)


    async def on_account_list(self, message: types.Message, state: FSMContext):
        print(message)

        if message.document:
            with io.BytesIO() as file:
                await message.bot.download(message.document.file_id, file)
                raw_links = file.read().decode('utf-8')
        else:
            raw_links = message.text

        links = account_checking.extract_links(raw_links)

        active, blocked, errors = await account_checking.check_urls(links)

        message_text = f'*Активних: {len(active)}\nЗаблокованих: {len(blocked)}\nПомилок перевірки: {len(errors)}*'
        message_files = []

        if len(active) <= 30:
            message_text += '\n\n*Активні акаунти:*\n' + '\n'.join(active)
        else:
            with io.BytesIO() as file:
                file.name = 'active_accounts.txt'
                file.write('\n'.join(active).encode('utf-8'))
                input_file = types.input_file.BufferedInputFile(file.getvalue(), filename=file.name)
                message_files.append(types.InputMediaDocument(media=input_file, caption='Активні акаунти'))

        if len(blocked) <= 30:
            message_text += '\n\n*Заблоковані акаунти:*\n' + '\n'.join(blocked)
        else:
            with io.BytesIO() as file:
                file.name = 'blocked_accounts.txt'
                file.write('\n'.join(blocked).encode('utf-8'))
                input_file = types.input_file.BufferedInputFile(file.getvalue(), filename=file.name)
                message_files.append(types.InputMediaDocument(media=input_file, caption='Заблоковані акаунти'))

        await message.answer(message_text, parse_mode='markdown')

        if message_files:
            await message.bot(SendMediaGroup(chat_id=message.chat.id, media=message_files))
        await state.clear()


    async def start_polling(self):
        await self.dp.start_polling(self.bot)

