import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from aiogram import Bot, Dispatcher, types, F, filters
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.methods import SendMediaGroup

from functions import account_checking, tiktok, twoFA, market_apps

import io

from .states import *
from .callbacks import EditAppsMenuCallback, DeleteAppCallback
from .middlewares import LangMiddleware
from .translations import translations as ts, handlers_variants
from . import storage

class ArbitrageBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.dp.update.middleware(LangMiddleware())

        self.http_session = aiohttp.ClientSession()

        self.register_handlers()

    def register_handlers(self):
        self.dp.message(filters.command.Command('start'))(self.start_msg)

        self.dp.message(F.text.lower().in_(handlers_variants('menu_check_accs')))(self.check_account_blocked)
        self.dp.message(F.text.lower().in_(handlers_variants('menu_2fa')))(self.start_2fa)
        self.dp.message(F.text.lower().in_(handlers_variants('menu_tiktok')))(self.tiktok_download_start)
        self.dp.message(F.text.lower().in_(handlers_variants('menu_apps')))(self.apps_menu)

        self.dp.message(Setup.choosing_lang)(self.set_lang)

        self.dp.message(CheckingAccounts.start_checking)(self.on_account_list)

        self.dp.message(TwoFA.key_input_msg)(self.get_2fa_msg)
        self.dp.message(TwoFA.key_input_callback)(self.get_2fa_msg)
        self.dp.callback_query(TwoFA.key_input_callback)(self.get_2fa_callback)

        self.dp.message(TikTokDownload.url_input)(self.tiktok_download)

        self.dp.callback_query(Apps.info_shown, EditAppsMenuCallback.filter(F.action == 'add'))(self.add_app_request)
        self.dp.callback_query(Apps.info_shown, EditAppsMenuCallback.filter(F.action == 'delete'))(self.delete_app_request)
        self.dp.message(Apps.entering_url)(self.add_app)
        self.dp.callback_query(Apps.selecting_to_delete)(self.delete_app)

    async def start_msg(self, message: types.Message, state: FSMContext):
        if not await storage.find_user(message.from_user.id):
            await storage.add_user(message.from_user.id)

        await message.answer("Виберіть мову / Выберите язык",
                             reply_markup=ReplyKeyboardBuilder()
                             .button(text='🇺🇦 Українська').button(text='🇷🇺 Русский').as_markup())

        await state.set_state(Setup.choosing_lang)

    async def set_lang(self, message: types.Message, state: FSMContext):
        lang = message.text
        if 'українська' in lang.lower():
            lang = 'ua'
        elif 'русский' in lang.lower():
            lang = 'ru'
        else:
            await message.answer('Неправильно вказана мова, спробуйте ще раз\nНеправильно указан язык, попробуйте еще раз')
            return
        await storage.set_lang(message.from_user.id, lang)

        kb = ReplyKeyboardBuilder()
        kb.button(text=ts[lang]['menu_check_accs'])
        kb.button(text=ts[lang]['menu_2fa'])
        kb.button(text=ts[lang]['menu_tiktok'])
        kb.button(text=ts[lang]['menu_apps'])
        kb.adjust(2)

        await message.answer(ts[lang]['start_msg'], reply_markup=kb.as_markup())

        await state.clear()


    async def check_account_blocked(self, message: types.Message, state: FSMContext, lang: str):
        await message.answer(ts[lang]['accs_ask_list'])
        await state.set_state(CheckingAccounts.start_checking)


    async def on_account_list(self, message: types.Message, state: FSMContext, lang: str):
        if message.document:
            with io.BytesIO() as file:
                await message.bot.download(message.document.file_id, file)
                raw_links = file.read().decode('utf-8')
        else:
            raw_links = message.text

        links = account_checking.extract_links(raw_links)

        active, blocked, errors = await account_checking.check_urls(links)

        message_text = ts[lang]['accs_info_msg'].format(len(active), len(blocked), len(errors))
        message_files = []

        if len(active) <= 30:
            message_text += f'\n\n*{ts[lang]["accs_active_label"]}:*\n' + '\n'.join(active)
        else:
            with io.BytesIO() as file:
                file.name = 'active_accounts.txt'
                file.write('\n'.join(active).encode('utf-8'))
                input_file = types.input_file.BufferedInputFile(file.getvalue(), filename=file.name)
                message_files.append(types.InputMediaDocument(media=input_file, caption=ts[lang]["accs_active_label"]))

        if len(blocked) <= 30:
            message_text += f'\n\n*{ts[lang]["accs_banned_label"]}:*\n' + '\n'.join(blocked)
        else:
            with io.BytesIO() as file:
                file.name = 'blocked_accounts.txt'
                file.write('\n'.join(blocked).encode('utf-8'))
                input_file = types.input_file.BufferedInputFile(file.getvalue(), filename=file.name)
                message_files.append(types.InputMediaDocument(media=input_file, caption=ts[lang]["accs_banned_label"]))

        await message.answer(message_text, parse_mode='markdown')

        if message_files:
            await message.bot(SendMediaGroup(chat_id=message.chat.id, media=message_files))
        await state.clear()

    async def start_2fa(self, message: types.Message, state: FSMContext, lang: str):
        keys = await storage.get_keys(message.from_user.id)
        keys = keys.split(' ') if keys else []
        if keys:
            inline = InlineKeyboardBuilder()
            for key in reversed(keys):
                inline.button(text=key, callback_data=key)
            inline.adjust(1)
            msg = await message.answer(ts[lang]['2fa_select_key'], reply_markup=inline.as_markup())
            await state.set_data({'select_key_msg': msg.message_id})
            await state.set_state(TwoFA.key_input_callback)
        else:
            await message.answer(ts[lang]['2fa_enter_key'])
            await state.set_state(TwoFA.key_input_msg)


    async def get_2fa_callback(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        key = callback.data
        await state.set_state(TwoFA.fetching_data)
        await callback.answer()

        await self.get_2fa(key, callback.message, state, lang)

    async def get_2fa_msg(self, message: types.Message, state: FSMContext, lang: str):
        key = message.text.strip()
        if twoFA.is_base32_encoded(key):
            await storage.add_key(message.from_user.id, key)
            await state.set_state(TwoFA.fetching_data)

            await self.get_2fa(key, message, state)
        else:
            await message.answer(ts[lang]['2fa_wrong_key'])
            await state.clear()

    async def get_2fa(self, key, message: types.Message, state: FSMContext, lang: str):
        state_data = await state.get_data()
        if 'select_key_msg' in state_data:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=state_data['select_key_msg'])

        while await state.get_state() == TwoFA.fetching_data:
            async with self.http_session.get(f'https://2fa.fb.rip/api/otp/{key}') as raw_response:
                response = await raw_response.json()

            if response['ok']:
                state_data = await state.get_data()
                if 'code_message_id' in state_data:
                    await message.bot.edit_message_text(chat_id=message.chat.id,
                                                        message_id=state_data['code_message_id'],
                                                        text=ts[lang]['2fa_code_msg'].format(
                                                            response['data']['otp'], response['data']['timeRemaining']),
                                                        parse_mode='markdown')
                else:
                    code_message = await message.answer(ts[lang]['2fa_code_msg'].format(
                                                            response['data']['otp'], response['data']['timeRemaining']),
                                                        parse_mode='markdown')
                    await state.set_data({'code_message_id': code_message.message_id})
                await asyncio.sleep(2)
            else:
                await message.answer(ts[lang]['wrong_key'])
                break

        state_data = await state.get_data()
        if 'code_message_id' in state_data:
            await message.bot.delete_message(chat_id=message.chat.id,
                                            message_id=state_data['code_message_id'])

    async def tiktok_download_start(self, message: types.Message, state: FSMContext, lang: str):
        await message.answer(ts[lang]['tiktok_ask_url'])
        await state.set_state(TikTokDownload.url_input)

    async def tiktok_download(self, message: types.Message, state: FSMContext, lang: str):
        url = message.text
        save_path = os.path.join(os.getcwd(), 'tiktok_videos')

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            video_path = await loop.run_in_executor(executor, tiktok.download_tiktok_video, url, save_path)
            print(video_path)

        if video_path:
            input_file = types.FSInputFile(video_path)
            await message.answer_document(input_file)
            os.remove(video_path)
        else:
            await message.answer(ts[lang]['tiktok_not_found'])
        await state.clear()


    async def apps_menu(self, message: types.Message, state: FSMContext, lang: str):
        users_apps = await storage.get_user_apps(message.from_user.id)
        for app in users_apps:
            if await market_apps.check_app(self.http_session, app.url):
                await storage.update_app_status(message.from_user.id, app.name, 'active')
                app.status = 'active'
            else:
                await storage.update_app_status(message.from_user.id, app.name, 'blocked')
                app.status = 'blocked'

        kb = InlineKeyboardBuilder()
        if len(users_apps) < 5:
            kb.button(text=ts[lang]['apps_add_button'], callback_data=EditAppsMenuCallback(action='add').pack())
        if users_apps:
            kb.button(text=ts[lang]['apps_delete_button'], callback_data=EditAppsMenuCallback(action='delete').pack())

        await state.set_state(Apps.info_shown)
        if not users_apps:
            await message.answer(ts[lang]['apps_no_apps'], reply_markup=kb.as_markup())
            return

        msg = ""
        for app in users_apps:
            msg += f"*{app.name}* "
            if app.status == 'active':
                msg += '✅\n'
            else:
                msg += '❌\n'

        await message.answer(msg, reply_markup=kb.as_markup(), parse_mode='markdown')


    async def add_app_request(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        await callback.answer()

        await self.bot.edit_message_text(chat_id=callback.message.chat.id,
                                         message_id=callback.message.message_id,
                                         text=ts[lang]['apps_ask_url'])

        await state.set_state(Apps.entering_url)

    async def add_app(self, message: types.Message, state: FSMContext, lang: str):
        url = message.text
        if 'play.google.com/store' not in url:
            await message.answer(ts[lang]['apps_bad_url'])
            await state.clear()

        app_name = await market_apps.get_app_name(self.http_session, url)
        if not app_name:
            await message.answer(ts[lang]['apps_already_blocked'])
            await state.clear()
            return
        elif await storage.find_app_by_name(message.from_user.id, app_name):
            await message.answer(ts[lang]['apps_added_yet'])
            await state.clear()
            return

        await storage.add_app(message.from_user.id, url, app_name)
        await message.answer(ts[lang]['apps_add_success'].format(app_name), parse_mode='markdown')
        await state.clear()


    async def delete_app_request(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        await callback.answer()

        users_apps = await storage.get_user_apps(callback.from_user.id)
        kb = InlineKeyboardBuilder()
        for app in users_apps:
            kb.button(text=app.name, callback_data=app.name)
        kb.adjust(1)

        await self.bot.edit_message_text(chat_id=callback.message.chat.id,
                                         message_id=callback.message.message_id,
                                         text=ts[lang]['apps_choose_delete'], reply_markup=kb.as_markup()
                                         )
        await state.set_state(Apps.selecting_to_delete)

    async def delete_app(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        app_name = callback.data
        await storage.delete_app(callback.from_user.id, app_name)
        await self.bot.edit_message_text(chat_id=callback.message.chat.id,
                                         message_id=callback.message.message_id,
                                         text=ts[lang]['apps_delete_success'].format(app_name),
                                         parse_mode='markdown')

        await callback.answer()
        await state.clear()

    async def check_apps_task(self):
        scheduler = AsyncIOScheduler()
        await self.check_apps()
        scheduler.add_job(self.check_apps, 'interval', minutes=30)
        scheduler.start()

    async def check_apps(self):
        users_apps = await storage.get_all_apps()
        for app in users_apps:
            if app.status == 'blocked':
                continue

            if not await market_apps.check_app(self.http_session, app.url):
                await storage.update_app_status(app.user_id, app.name, 'blocked')
                lang = await storage.get_lang(app.user_id)
                await self.bot.send_message(app.user_id, ts[lang]['apps_blocked_warning'].format(app.name),
                                            parse_mode='markdown')

        print('Apps checked')

    async def start_polling(self):
        await self.dp.start_polling(self.bot)

