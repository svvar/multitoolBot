from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot.core.storage.main_storage import get_user_balance

check_balance_router = Router()

@check_balance_router.message(F.text == __("💰 Управлiння балансом"))
async def check_user_balance(message: Message):

    balance = await get_user_balance(message.from_user.id)
    replenish_balance = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=_("💰 Поповнити баланс"), callback_data="replenish_balance")]])

    await message.answer(_(f"Ваш баланс: {balance}"), reply_markup=replenish_balance)

@check_balance_router.callback_query(F.data == "replenish_balance")
async def replenish_balance_func(callback: CallbackQuery):

    await callback.message.answer(_("✍️ Для поповнення балансу напишіть сапорту @mustage_support (можлива оплата в USDT): Привіт, хочу поповнити баланс у роботі @mustage_service_bot на {сумма_поповнення} $."))
