import asyncio
import random
from datetime import datetime
import io
import os
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from aiogram import Bot, Dispatcher, types, F, filters
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.methods import SendMediaGroup

from functions import account_checking, downloader, twoFA, market_apps, id_generator, image_uniqueizer, video_uniqueizer

from .states import *
from .callbacks import EditAppsMenuCallback
from .middlewares import LangMiddleware
from .translations import translations as ts, handlers_variants
from . import storageV2 as storage


class ArbitrageBot:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.dp = Dispatcher()
        self.dp.update.middleware(LangMiddleware())


        self.http_session = aiohttp.ClientSession()
        self.uniqualization_semaphore = asyncio.Semaphore(5)
        self.id_semaphore = asyncio.Semaphore(5)
        self.tiktok_semaphore = asyncio.Semaphore(3)

        self.load_start_msg()
        self.register_handlers()

    def register_handlers(self):
        self.dp.message(filters.command.Command('start'))(self.start_msg)

        self.dp.message(F.text.lower().in_(handlers_variants('menu_check_accs')))(self.check_account_blocked)
        self.dp.message(F.text.lower().in_(handlers_variants('menu_2fa')))(self.start_2fa)
        self.dp.message(F.text.lower().in_(handlers_variants('menu_tiktok')))(self.tiktok_download_start)
        self.dp.message(F.text.lower().in_(handlers_variants('menu_apps')))(self.apps_menu)
        self.dp.message(F.text.lower().in_(handlers_variants('menu_id')))(self.id_gen_start)
        self.dp.message(F.text.lower().in_(handlers_variants('menu_unique')))(self.unique_ask_media)

        self.dp.message(F.text.lower().in_(handlers_variants('to_menu')))(self.show_menu)

        self.dp.message(Setup.choosing_lang)(self.set_lang)

        self.dp.message(CheckingAccounts.start_checking, F.text.lower().in_(handlers_variants('accs_check')))(self.check_links)
        self.dp.message(CheckingAccounts.start_checking)(self.on_links_message)


        self.dp.message(TwoFA.key_input_msg)(self.get_2fa_msg)
        self.dp.message(TwoFA.key_input_callback)(self.get_2fa_msg)
        self.dp.callback_query(TwoFA.key_input_callback)(self.get_2fa_callback)

        self.dp.message(TikTokDownload.url_input)(self.tiktok_download)

        self.dp.callback_query(Apps.info_shown, EditAppsMenuCallback.filter(F.action == 'add'))(self.add_app_request)
        self.dp.callback_query(Apps.info_shown, EditAppsMenuCallback.filter(F.action == 'delete'))(self.delete_app_request)
        self.dp.message(Apps.entering_url)(self.add_app)
        self.dp.callback_query(Apps.selecting_to_delete)(self.delete_app)

        self.dp.message(IdGenerator.need_meta)(self.id_gen_photo_ask)
        self.dp.message(IdGenerator.selecting_photo)(self.id_gen_color)
        self.dp.message(IdGenerator.selecting_color)(self.id_gen_sex)
        self.dp.message(IdGenerator.selecting_sex)(self.id_gen_name)
        self.dp.message(IdGenerator.entering_name)(self.id_gen_age)
        self.dp.message(IdGenerator.entering_age)(self.id_gen_final)
        self.dp.message(IdGenerator.generating, F.text.lower().in_(handlers_variants('one_more')))(self.id_generate)

        self.dp.message(Uniquilizer.media_input)(self.unique_save_media)
        self.dp.message(Uniquilizer.copies_num)(self.unique_num_copies)
        self.dp.message(Uniquilizer.generating)(self.unique_generate)

    def load_start_msg(self):
        contents = os.listdir('./downloads/admin_welcome')
        if 'text.txt' not in contents and 'media_id.txt' not in contents and 'links.txt' not in contents:
            self.welcome_text = None
            self.welcome_media_id = None
            self.welcome_links = None
            return

        with open('./downloads/admin_welcome/text.txt', 'r') as msg_f:
            msg = msg_f.read()
            self.welcome_text = msg.strip()

        with open('./downloads/admin_welcome/media_id.txt', 'r') as media_f:
            media_id = media_f.read()
            self.welcome_media_id = media_id.strip()

        with open('./downloads/admin_welcome/links.txt', 'r') as links_f:
            links = links_f.read()
            self.welcome_links = links.strip()


    async def send_custom_welcome_message(self, message: types.Message):
        url_kb = None

        if not self.welcome_text and not self.welcome_media_id:
            return

        if self.welcome_links:
            url_kb = InlineKeyboardBuilder()
            for link in self.welcome_links.split('\n'):
                url_kb.button(text=link.rsplit(' ', 1)[0], url=link.rsplit(' ', 1)[1])
            url_kb.adjust(1)

        if self.welcome_media_id and url_kb:
            media_type = self.welcome_media_id.split(' ')[0]
            media_id = self.welcome_media_id.split(' ')[1]
            if media_type == 'photo':
                await message.answer_photo(photo=media_id, caption=self.welcome_text, reply_markup=url_kb.as_markup())
            elif media_type == 'video':
                await message.answer_video(video=media_id, caption=self.welcome_text, reply_markup=url_kb.as_markup())
        elif url_kb:
            await message.answer(self.welcome_text, reply_markup=url_kb.as_markup())
        elif self.welcome_media_id:
            media_type = self.welcome_media_id.split(' ')[0]
            media_id = self.welcome_media_id.split(' ')[1]
            if media_type == 'photo':
                await message.answer_photo(photo=media_id, caption=self.welcome_text)
            elif media_type == 'video':
                await message.answer_video(video=media_id, caption=self.welcome_text)
        else:
            await message.answer(self.welcome_text)


    async def start_msg(self, message: types.Message, state: FSMContext):
        if not await storage.find_user(message.from_user.id):
            user = message.from_user
            await storage.add_user(user.id, user.first_name, user.last_name, user.username, user.language_code)

        await self.send_custom_welcome_message(message)
        await message.answer("Виберіть мову / Выберите язык / Select language:",
                             reply_markup=ReplyKeyboardBuilder()
                             .button(text='🇺🇦 Українська').button(text='🇷🇺 Русский').button(text='🇺🇸 English').as_markup(resize_keyboard=True))

        await state.set_state(Setup.choosing_lang)

    async def set_lang(self, message: types.Message, state: FSMContext):
        lang = message.text
        if 'українська' in lang.lower():
            lang = 'uk'
        elif 'русский' in lang.lower():
            lang = 'ru'
        elif 'english' in lang.lower():
            lang = 'en'
        else:
            await message.answer('Неправильно вказана мова, спробуйте ще раз\nНеправильно указан язык, попробуйте еще раз')
            return
        await storage.set_lang(message.from_user.id, lang)
        await self.show_menu(message, state, lang)

    async def show_menu(self, message: types.Message, state: FSMContext, lang: str):

        kb = ReplyKeyboardBuilder()
        kb.button(text=ts[lang]['menu_check_accs'])
        kb.button(text=ts[lang]['menu_2fa'])
        kb.button(text=ts[lang]['menu_tiktok'])
        kb.button(text=ts[lang]['menu_apps'])
        kb.button(text=ts[lang]['menu_id'])
        kb.button(text=ts[lang]['menu_unique'])
        kb.adjust(2)

        await message.answer(ts[lang]['start_msg'], reply_markup=kb.as_markup(resize_keyboard=True))
        await state.clear()


    async def check_account_blocked(self, message: types.Message, state: FSMContext, lang: str):
        kb = ReplyKeyboardBuilder()
        kb.button(text=ts[lang]['accs_check'])
        kb.button(text=ts[lang]['to_menu'])
        kb.adjust(1)


        await message.answer(ts[lang]['accs_ask_list'], reply_markup=kb.as_markup(resize_keyboard=True))
        await state.set_state(CheckingAccounts.start_checking)
        await state.update_data({'messages': [], 'txt': None})


    async def on_links_message(self, message: types.Message, state: FSMContext, lang: str):
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
                await message.answer(ts[lang]['accs_too_long'])
                await state.clear()
                await self.show_menu(message, state, lang)

            messages.append(message.text)
            await state.update_data({'messages': messages})


    async def check_links(self, message: types.Message, state: FSMContext, lang: str):
        state_data = await state.get_data()
        messages = '\n'.join(state_data['messages'])
        txt = state_data['txt']

        raw_links = txt if txt else messages

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
        await self.show_menu(message, state, lang)

    async def rotate_proxy_task(self, rotate_url):
        await self.rotate_proxy(rotate_url)
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.rotate_proxy, 'interval', minutes=3, args=(rotate_url,))
        scheduler.start()

    async def rotate_proxy(self, rotate_url):
        print('Rotating proxy...')
        try:
            async with self.http_session.get(rotate_url, ssl=False, timeout=15) as response:
                if response.status == 200:
                    print('Proxy rotated')
                    return True
                print('Proxy rotation failed')
                return False
        except asyncio.TimeoutError:
            print('Proxy rotation failed')
            return False

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
        key = message.text.strip().replace(' ', '')
        if twoFA.is_base32_encoded(key):
            await storage.add_key(message.from_user.id, key)
            await state.set_state(TwoFA.fetching_data)

            await self.get_2fa(key, message, state, lang)
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
        if 'tiktok.com' not in url:
            await message.answer(ts[lang]['tiktok_bad_url'])
            await state.clear()
            return

        # Clearing state early here to make other commands work correctly while downloading tiktok
        await state.clear()

        await message.answer(ts[lang]['tiktok_wait'])

        async with self.tiktok_semaphore:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=7) as executor:
                download_folder = os.path.abspath('./downloads')
                video_path = await loop.run_in_executor(executor, downloader.save_tiktok_video, url, download_folder)

        if video_path:
            input_file = types.FSInputFile(video_path)
            await message.answer_document(input_file)
            os.remove(video_path)
        else:
            await message.answer(ts[lang]['tiktok_not_found'])


    async def apps_menu(self, message: types.Message, state: FSMContext, lang: str):
        users_apps = await storage.get_user_apps(message.from_user.id)
        for app in users_apps:
            if await market_apps.check_app(self.http_session, app.url):
                await storage.update_app_status(app.id, 'active')
                app.status = 'active'
            else:
                await storage.update_app_status(app.id, 'blocked')
                await message.answer(ts[lang]['apps_blocked_warning'].format(app.app_name), parse_mode='markdown')
                app.status = 'blocked'

        kb = InlineKeyboardBuilder()
        if len(users_apps) < 20:
            kb.button(text=ts[lang]['apps_add_button'], callback_data=EditAppsMenuCallback(action='add').pack())
        if users_apps:
            kb.button(text=ts[lang]['apps_delete_button'], callback_data=EditAppsMenuCallback(action='delete').pack())

        await state.set_state(Apps.info_shown)
        if not users_apps:
            await message.answer(ts[lang]['apps_no_apps'], reply_markup=kb.as_markup())
            return

        msg = ""
        for app in users_apps:
            msg += f"*{app.app_name}* "
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
        url_app_id = market_apps.extract_id(url)
        url = f'https://play.google.com/store/apps/details?id={url_app_id}'

        if not app_name:
            await message.answer(ts[lang]['apps_already_blocked'])
            await state.clear()
            return

        app_id = await storage.get_app_id_by_url_app_id(url_app_id)
        if await storage.find_app_by_app_id(app_id, message.from_user.id):
            await message.answer(ts[lang]['apps_added_yet'])
            await state.clear()
            return

        app_id = await storage.add_app(url_app_id, app_name, url)
        await storage.add_app_user(app_id, message.from_user.id)
        await message.answer(ts[lang]['apps_add_success'].format(app_name), parse_mode='markdown')
        await state.clear()


    async def delete_app_request(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        await callback.answer()

        users_apps = await storage.get_user_apps(callback.from_user.id)
        kb = InlineKeyboardBuilder()
        for app in users_apps:
            kb.button(text=app.app_name, callback_data=str(app.id))
        kb.adjust(1)

        await self.bot.edit_message_text(chat_id=callback.message.chat.id,
                                         message_id=callback.message.message_id,
                                         text=ts[lang]['apps_choose_delete'], reply_markup=kb.as_markup()
                                         )
        await state.set_state(Apps.selecting_to_delete)

    async def delete_app(self, callback: types.CallbackQuery, state: FSMContext, lang: str):
        app_id = int(callback.data)                      # id field in Apps table; NOT url_app_id field
        app_name = await storage.get_app_name(app_id)
        await storage.delete_app_user(app_id, callback.from_user.id)
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
        print('Checking apps...')
        users_apps = await storage.get_all_apps()
        for app in users_apps:
            if app.status == 'blocked':
                continue

            if not await market_apps.check_app(self.http_session, app.url):
                await storage.update_app_status(app.id, 'blocked')
                users = await storage.get_users_of_app(app.id)
                for user in users:
                    lang = await storage.get_lang(user)
                    await self.bot.send_message(user, ts[lang]['apps_blocked_warning'].format(app.app_name),
                                                parse_mode='markdown')

        print('Apps checked')


    async def _check_apps_2_WIP(self):
        print('Checking apps...')
        users_apps = await storage.get_all_apps()

        to_check = []
        for app in users_apps:
            if app.status == 'blocked':
                continue

            to_check.append(app.url)

        print('Apps checked')


    async def id_gen_start(self, message: types.Message, state: FSMContext, lang: str):
        reply_kb = ReplyKeyboardBuilder()
        reply_kb.button(text=ts[lang]['no_meta'])
        reply_kb.button(text=ts[lang]['random_meta'])
        reply_kb.button(text=ts[lang]['to_menu'])
        reply_kb.adjust(2)

        await message.answer(ts[lang]['ask_meta'], reply_markup=reply_kb.as_markup(resize_keyboard=True))
        await state.set_state(IdGenerator.need_meta)

    async def id_gen_photo_ask(self, message: types.Message, state: FSMContext, lang: str):
        meta = message.text
        if meta.lower() == ts[lang]['no_meta'].lower():
            await state.update_data({'meta': False})
        elif meta.lower() == ts[lang]['random_meta'].lower():
            await state.update_data({'meta': True})
        else:
            await message.answer(ts[lang]['repeat_input'])
            return


        reply_kb = ReplyKeyboardBuilder()
        reply_kb.button(text=ts[lang]['random_photo'])
        reply_kb.button(text=ts[lang]['to_menu'])
        reply_kb.adjust(2)

        await message.answer(ts[lang]['ask_photo'], reply_markup=reply_kb.as_markup(resize_keyboard=True))
        await state.set_state(IdGenerator.selecting_photo)


    async def id_gen_color(self, message: types.Message, state: FSMContext, lang: str):
        if message.photo:
            photo_id = message.photo[-1].file_id
            photo_file = await self.bot.get_file(photo_id)
            file_unique_id = message.photo[-1].file_unique_id
            file_path = photo_file.file_path

            await self.bot.download_file(file_path, f'./faces/temp/{file_unique_id}.jpg')
            await state.update_data({'photo_path': f'./faces/temp/{file_unique_id}.jpg'})
        elif message.document and message.document.mime_type.startswith('image'):
            photo_id = message.document.file_id
            photo_file = await self.bot.get_file(photo_id)
            file_unique_id = message.document.file_unique_id
            file_name = message.document.file_name
            file_path = photo_file.file_path

            await self.bot.download_file(file_path, f'./faces/temp/{file_unique_id}.{file_name.split(".")[-1]}')
            await state.update_data({'photo_path': f'./faces/temp/{file_unique_id}.{file_name.split(".")[-1]}'})
        elif message.text and message.text.lower() == ts[lang]['random_photo'].lower():
            await state.update_data({'photo_path': None})
        else:
            await message.answer(ts[lang]['repeat_input'])
            return



        reply_kb = ReplyKeyboardBuilder()
        reply_kb.button(text=ts[lang]['color'])
        reply_kb.button(text=ts[lang]['black_white'])
        reply_kb.button(text=ts[lang]['to_menu'])
        reply_kb.adjust(2)

        await message.answer(ts[lang]['select_photo_color'], reply_markup=reply_kb.as_markup(resize_keyboard=True))
        await state.set_state(IdGenerator.selecting_color)

    async def id_gen_sex(self, message: types.Message, state: FSMContext, lang: str):
        color = message.text
        if color.lower() == ts[lang]['color'].lower():
            await state.update_data({'grey': False})
        elif color.lower() == ts[lang]['black_white'].lower():
            await state.update_data({'grey': True})
        else:
            await message.answer(ts[lang]['repeat_input'])
            return

        state_data = await state.get_data()
        if state_data['photo_path']:
            kb = ReplyKeyboardBuilder()
            kb.button(text=ts[lang]['to_menu'])
            await message.answer(ts[lang]['enter_name'], reply_markup=kb.as_markup(resize_keyboard=True))
            await state.set_state(IdGenerator.entering_name)
        else:
            reply_kb = ReplyKeyboardBuilder()
            reply_kb.button(text=ts[lang]['man'])
            reply_kb.button(text=ts[lang]['woman'])
            reply_kb.button(text=ts[lang]['to_menu'])
            reply_kb.adjust(2)

            await message.answer(ts[lang]['select_sex'], reply_markup=reply_kb.as_markup(resize_keyboard=True))
            await state.set_state(IdGenerator.selecting_sex)

    async def id_gen_name(self, message: types.Message, state: FSMContext, lang: str):
        sex = message.text
        if sex.lower() == ts[lang]['man'].lower():
            await state.update_data({'sex': 'male'})
        elif sex.lower() == ts[lang]['woman'].lower():
            await state.update_data({'sex': 'female'})
        else:
            await message.answer(ts[lang]['repeat_input'])
            return

        kb = ReplyKeyboardBuilder()
        kb.button(text=ts[lang]['to_menu'])
        await message.answer(ts[lang]['enter_name'], reply_markup=kb.as_markup(resize_keyboard=True))
        await state.set_state(IdGenerator.entering_name)


    async def id_gen_age(self, message: types.Message, state: FSMContext, lang: str):
        name = message.text.split(' ')
        if len(name) != 2:
            await message.answer(ts[lang]['repeat_input'])
            return

        await state.update_data({'name': name[0], 'surname': name[1]})

        kb = ReplyKeyboardBuilder()
        kb.button(text=ts[lang]['to_menu'])
        await message.answer(ts[lang]['enter_age'], reply_markup=kb.as_markup(resize_keyboard=True))
        await state.set_state(IdGenerator.entering_age)

    async def id_gen_final(self, message: types.Message, state: FSMContext, lang: str):
        age = message.text
        try:
            age = datetime.strptime(age, '%d.%m.%Y')
            await state.update_data({'day': age.day, 'month': age.month, 'year': age.year})
            await state.set_state(IdGenerator.generating)
            await self.id_generate(message, state, lang)
        except ValueError:
            await message.answer(ts[lang]['repeat_input'])
            return


    async def id_generate(self, message: types.Message, state: FSMContext, lang: str):
        kb = ReplyKeyboardBuilder()
        kb.button(text=ts[lang]['to_menu'])

        await message.answer(ts[lang]['wait_generating'], reply_markup=kb.as_markup(resize_keyboard=True))
        stored_data = await state.get_data()
        account = id_generator.Account(stored_data['name'], stored_data['surname'], stored_data['day'], stored_data['month'], stored_data['year'])

        if not stored_data['photo_path']:

            if stored_data['sex'] == 'male':
                photo_dir = './faces/male'
            else:
                photo_dir = './faces/female'

            photo_path = os.path.join(photo_dir, random.choice(os.listdir(photo_dir)))
            kb.button(text=ts[lang]['one_more'])
        else:
            photo_path = stored_data['photo_path']

        result_path = os.path.join('./faces', f'{account.name}_{account.surname}{message.message_id}.jpg')

        async with self.id_semaphore:
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
            await message.answer(ts[lang]['id_gen_err'], reply_markup=kb.as_markup(resize_keyboard=True))

        if stored_data['photo_path']:
            os.remove(photo_path)

    async def unique_ask_media(self, message: types.Message, state: FSMContext, lang: str):
        kb = ReplyKeyboardBuilder()
        kb.button(text=ts[lang]['to_menu'])

        await message.answer(ts[lang]['unique_ask_media'], reply_markup=kb.as_markup(resize_keyboard=True))
        await state.set_state(Uniquilizer.media_input)


    async def unique_save_media(self, message: types.Message, state: FSMContext, lang: str):
        if message.photo:
            photo_id = message.photo[-1].file_id
            file_unique_id = message.photo[-1].file_unique_id
            photo_file = await self.bot.get_file(photo_id)
            file_path = photo_file.file_path

            os.makedirs(f'./downloads/{file_unique_id}', exist_ok=True)
            await self.bot.download_file(file_path, f'./downloads/{file_unique_id}/{file_unique_id}.jpg')
            await state.update_data({'photo_path': f'./downloads/{file_unique_id}/{file_unique_id}.jpg'})
        elif message.video:
            video_id = message.video.file_id
            file_unique_id = message.video.file_unique_id
            video_file = await self.bot.get_file(video_id)
            file_path = video_file.file_path

            os.makedirs(f'./downloads/{file_unique_id}', exist_ok=True)
            await self.bot.download_file(file_path, f'./downloads/{file_unique_id}/{file_unique_id}.mp4')
            await state.update_data({'video_path': f'./downloads/{file_unique_id}/{file_unique_id}.mp4'})
        elif message.document:
            doc_id = message.document.file_id
            file_unique_id = message.document.file_unique_id

            if message.document.file_size > 20 * 1024 * 1024:
                await message.answer(ts[lang]['unique_file_too_large'])
                return

            doc_file = await self.bot.get_file(doc_id)
            file_path = doc_file.file_path
            file_name = message.document.file_name

            if file_name.lower().endswith('.jpg') or file_name.lower().endswith('.jpeg') or file_name.lower().endswith('.png'):
                os.makedirs(f'./downloads/{file_unique_id}', exist_ok=True)
                await self.bot.download_file(file_path, f'./downloads/{file_unique_id}/{file_name}')
                await state.update_data({'photo_path': f'./downloads/{file_unique_id}/{file_name}'})

            elif file_name.lower().endswith('.mp4') or file_name.lower().endswith('.mov'):
                os.makedirs(f'./downloads/{file_unique_id}', exist_ok=True)
                await self.bot.download_file(file_path, f'./downloads/{file_unique_id}/{file_name}')
                await state.update_data({'video_path': f'./downloads/{file_unique_id}/{file_name}'})
            else:
                await message.answer(ts['lang']['unique_unsupp_format'])
                return

        else:
            await message.answer(ts['lang']['unique_send_media'])
            return

        await message.answer(ts[lang]['unique_ask_copies'])
        await state.set_state(Uniquilizer.copies_num)

    async def unique_num_copies(self, message: types.Message, state: FSMContext, lang: str):
        data = await state.get_data()

        media_type = 'photo' if 'photo_path' in data else 'video'

        if not message.text.isdigit():
            await message.answer(ts['lang']['unique_ask_copies'])
            return
        if media_type == 'photo' and int(message.text) > 20 or int(message.text) < 1:
            await message.answer(ts['lang']['unique_ask_copies'])
            return
        elif media_type == 'video' and int(message.text) > 5 or int(message.text) < 1:
            await message.answer(ts['lang']['unique_ask_copies'])
            return

        copies = int(message.text)

        await state.update_data({'copies': copies})
        await message.answer(ts[lang]['unique_wait'])
        await state.set_state(Uniquilizer.generating)
        await self.unique_generate(message, state, lang)


    async def unique_generate(self, message: types.Message, state: FSMContext, lang: str):
        async with self.uniqualization_semaphore:
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


    async def start_polling(self):
        print("Starting bot")
        await self.dp.start_polling(self.bot)

    def include_router(self, router):
        self.dp.include_router(router)

