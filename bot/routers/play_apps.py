import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.core.states import Apps
from bot.core.callbacks import EditAppsMenuCallback
from bot.core.storage import main_storage as storage
from bot.functions import market_apps
from bot.core.locale_helper import translate_string


play_apps_router = Router()


@play_apps_router.message(F.text == __('📱 Додатки Google Play'))
async def apps_menu(message: types.Message, state: FSMContext):
    http_session = message.bot.http_session

    users_apps = await storage.get_user_apps(message.from_user.id)
    tasks = [market_apps.check_app(http_session, app) for app in users_apps]
    results = await asyncio.gather(*tasks)

    banned_tasks = [market_apps.check_app(http_session, app) for app, status in results if not status]
    banned_results = await asyncio.gather(*banned_tasks)

    for app, status in banned_results:
        await storage.update_app_status(app.id, 'blocked')
        users = await storage.get_users_of_app(app.id)
        for user in users:
            lang = await storage.get_lang(user)
            await message.bot.send_message(user, _('🚨 УВАГА! Ваш додаток *{}* заблоковано').format(app.app_name),
                                            parse_mode='markdown')

    kb = InlineKeyboardBuilder()
    if len(users_apps) < 15:
        kb.button(text=_('Додати додаток'), callback_data=EditAppsMenuCallback(action='add').pack())
    if users_apps:
        kb.button(text=_('Видалити додаток'), callback_data=EditAppsMenuCallback(action='delete').pack())

    await state.set_state(Apps.info_shown)
    if not users_apps:
        await message.answer(_('У вас немає додатків для сповіщення про блокування в Google Play'), reply_markup=kb.as_markup())
        return

    final_results = banned_results
    final_results.extend([(app, status) for app, status in results if status])
    msg = ""
    for app, status in final_results:
        msg += f"*{app.app_name}* "
        if status:
            msg += '✅\n'
        else:
            msg += '❌\n'

    await message.answer(msg, reply_markup=kb.as_markup(), parse_mode='markdown')


@play_apps_router.callback_query(Apps.info_shown, EditAppsMenuCallback.filter(F.action == 'add'))
async def add_app_request(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    await callback.bot.edit_message_text(chat_id=callback.message.chat.id,
                                        message_id=callback.message.message_id,
                                        text=_('Введіть посилання на додаток в Google Play'))

    await state.set_state(Apps.entering_url)


@play_apps_router.message(Apps.entering_url)
async def add_app(message: types.Message, state: FSMContext):
    http_session = message.bot.http_session

    url = message.text
    if 'play.google.com/store' not in url:
        await message.answer(_('Непідохдяще посилання, введіть посилання на додаток в Google Play'))
        await state.clear()

    app_name = await market_apps.get_app_name(http_session, url)
    url_app_id = market_apps.extract_id(url)
    url = f'https://play.google.com/store/apps/details?id={url_app_id}'

    if not app_name:
        await message.answer(_('Ви намагаєтесь додати вже заблокований додаток або такого не існувало'))
        await state.clear()
        return

    app_id = await storage.get_app_id_by_url_app_id(url_app_id)
    if await storage.find_app_by_app_id(app_id, message.from_user.id):
        await message.answer(_('Додаток вже додано'))
        await state.clear()
        return

    app_id = await storage.add_app(url_app_id, app_name, url)
    await storage.add_app_user(app_id, message.from_user.id)
    await message.answer(_('Додаток *{}* успішно додано').format(app_name), parse_mode='markdown')
    await state.clear()


@play_apps_router.callback_query(Apps.info_shown, EditAppsMenuCallback.filter(F.action == 'delete'))
async def delete_app_request(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    users_apps = await storage.get_user_apps(callback.from_user.id)
    kb = InlineKeyboardBuilder()
    for app in users_apps:
        kb.button(text=app.app_name, callback_data=str(app.id))
    kb.adjust(1)

    await callback.bot.edit_message_text(chat_id=callback.message.chat.id,
                                         message_id=callback.message.message_id,
                                         text=_('Виберіть додаток для видалення:'),
                                         reply_markup=kb.as_markup()
                                         )
    await state.set_state(Apps.selecting_to_delete)


@play_apps_router.callback_query(Apps.selecting_to_delete)
async def delete_app(callback: types.CallbackQuery, state: FSMContext):
    app_id = int(callback.data)                      # id field in Apps table; NOT url_app_id field
    app_name = await storage.get_app_name(app_id)
    await storage.delete_app_user(app_id, callback.from_user.id)
    await callback.bot.edit_message_text(chat_id=callback.message.chat.id,
                                         message_id=callback.message.message_id,
                                         text=_('Додаток *{}* видалено').format(app_name),
                                         parse_mode='markdown')

    await callback.answer()
    await state.clear()


async def check_apps_task(bot):
    scheduler = AsyncIOScheduler()
    await check_apps(bot)
    scheduler.add_job(check_apps, 'interval', minutes=30, args=[bot])
    scheduler.start()


async def check_apps(bot):
    print('Checking apps...')
    semaphore = asyncio.Semaphore(10)

    # limit max number of concurrent checks
    async def semaphore_check_app(app):
        async with semaphore:
            return await market_apps.check_app(bot.http_session, app)

    # first check - all apps
    users_apps = await storage.get_all_apps()
    to_check = [app for app in users_apps if app.status != 'blocked']
    tasks = [semaphore_check_app(app) for app in to_check]
    results = await asyncio.gather(*tasks)

    # second check - only failed apps
    to_check = [app for app, status in results if not status]
    retry_banned = [semaphore_check_app(app) for app in to_check]
    results = await asyncio.gather(*retry_banned)

    # if failed again - update status and notify users
    for app, status in results:
        if not status:
            await storage.update_app_status(app.id, 'blocked')
            users = await storage.get_users_of_app(app.id)
            for user in users:
                lang = await storage.get_lang(user)
                await bot.send_message(user,
                                       translate_string(lang, "🚨 УВАГА! Ваш додаток *{}* заблоковано").format(app.app_name),
                                        parse_mode='markdown')

    print('Apps checked')
