
from aiogram import types, Router, filters, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram.fsm.context import FSMContext

from bot.core.states import Setup
from bot.core.storage import main_storage as storage


main_menu_router = Router()


@main_menu_router.message(filters.command.CommandStart())
async def start_msg(message: types.Message, state: FSMContext):
    if not await storage.find_user(message.from_user.id):
        user = message.from_user
        await storage.add_user(user.id, user.first_name, user.last_name, user.username, user.language_code)

    await send_custom_welcome_message(message)
    await message.answer("Виберіть мову / Выберите язык / Select language:",
                         reply_markup=ReplyKeyboardBuilder()
                         .button(text='🇺🇦 Українська').button(text='🇷🇺 Русский').button(text='🇺🇸 English').as_markup(resize_keyboard=True))

    await state.set_state(Setup.choosing_lang)


@main_menu_router.message(Setup.choosing_lang)
async def set_lang(message: types.Message, state: FSMContext):
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
    await show_menu(message, state)


@main_menu_router.message(F.text == __('🏠 В меню'))
async def show_menu(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardBuilder()
    kb.button(text=_('✅️ Перевірити FB акаунти на блокування'))
    kb.button(text=_('🔒 2fa код'))
    kb.button(text=_('📹 Завантажити відео з TikTok'))
    kb.button(text=_('📱 Додатки Google Play'))
    kb.button(text=_('🆔 Генератор ID'))
    kb.button(text=_('🕶️ Унікалізувати фото чи відео'))
    kb.button(text=_('🚀 Фармерам'))
    kb.button(text=_('🤳 Генератор селфі'))
    kb.button(text=_('📝 Верифікація БМ (укр.)'))
    kb.button(text=_('📝 Верифікація TikTok (бізнес акк.)'))
    kb.adjust(2)

    await message.answer(_('Виберіть дію з меню:'), reply_markup=kb.as_markup(resize_keyboard=True))
    await state.clear()


async def send_custom_welcome_message(message: types.Message):
    url_kb = None

    welcome_message = await storage.get_start_msg()
    welcome_text = welcome_message.welcome_text if welcome_message else None
    welcome_media_id = welcome_message.welcome_media_id if welcome_message else None
    welcome_links = welcome_message.welcome_links if welcome_message else None

    if not welcome_text and not welcome_media_id:
        return

    if welcome_links:
        url_kb = InlineKeyboardBuilder()
        for link in welcome_links.split('\n'):
            url_kb.button(text=link.rsplit(' ', 1)[0], url=link.rsplit(' ', 1)[1])
        url_kb.adjust(1)

    if welcome_media_id and url_kb:
        media_type = welcome_media_id.split(' ')[0]
        media_id = welcome_media_id.split(' ')[1]
        if media_type == 'photo':
            await message.answer_photo(photo=media_id, caption=welcome_text, reply_markup=url_kb.as_markup())
        elif media_type == 'video':
            await message.answer_video(video=media_id, caption=welcome_text, reply_markup=url_kb.as_markup())
    elif url_kb:
        await message.answer(welcome_text, reply_markup=url_kb.as_markup())
    elif welcome_media_id:
        media_type = welcome_media_id.split(' ')[0]
        media_id = welcome_media_id.split(' ')[1]
        if media_type == 'photo':
            await message.answer_photo(photo=media_id, caption=welcome_text)
        elif media_type == 'video':
            await message.answer_video(video=media_id, caption=welcome_text)
    else:
        await message.answer(welcome_text)