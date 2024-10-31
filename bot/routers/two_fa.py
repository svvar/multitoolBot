import asyncio

from aiogram import types, Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __


from bot.core.states import TwoFA
from bot.core.storage import main_storage as storage
from bot.functions import twoFA

two_fa_router = Router()


@two_fa_router.message(F.text == __('🔒 2fa код'))
async def start_2fa(message: types.Message, state: FSMContext):
    keys = await storage.get_keys(message.from_user.id)
    keys = keys.split(' ') if keys else []
    if keys:
        inline = InlineKeyboardBuilder()
        for key in reversed(keys):
            inline.button(text=key, callback_data=key)
        inline.adjust(1)
        msg = await message.answer(_('Введіть ключ для 2fa або виберіть з нещодавніх:'), reply_markup=inline.as_markup())
        await state.set_data({'select_key_msg': msg.message_id})
        await state.set_state(TwoFA.key_input_callback)
    else:
        await message.answer(_('Введіть ключ для 2fa:'))
        await state.set_state(TwoFA.key_input_msg)


@two_fa_router.callback_query(TwoFA.key_input_callback)
async def get_2fa_callback(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data
    await state.set_state(TwoFA.fetching_data)
    await callback.answer()

    await get_2fa(key, callback.message, state)


@two_fa_router.message(TwoFA.key_input_msg)
@two_fa_router.message(TwoFA.key_input_callback)
async def get_2fa_msg(message: types.Message, state: FSMContext):
    key = message.text.strip().replace(' ', '')
    if twoFA.is_base32_encoded(key):
        await storage.add_key(message.from_user.id, key)
        await state.set_state(TwoFA.fetching_data)

        await get_2fa(key, message, state)
    else:
        await message.answer(_('Неправильний ключ'))
        await state.clear()


async def get_2fa(key, message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    if 'select_key_msg' in state_data:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=state_data['select_key_msg'])

    while await state.get_state() == TwoFA.fetching_data:
        async with message.bot.http_session.get(f'https://2fa.fb.rip/api/otp/{key}') as raw_response:
            response = await raw_response.json()

        if response['ok']:
            state_data = await state.get_data()
            if 'code_message_id' in state_data:
                await message.bot.edit_message_text(chat_id=message.chat.id,
                                                    message_id=state_data['code_message_id'],
                                                    text=_('Ваш код: `{}` \nТермін дії: {} секунд').format(
                                                        response['data']['otp'], response['data']['timeRemaining']),
                                                    parse_mode='markdown')
            else:
                code_message = await message.answer(_('Ваш код: `{}` \nТермін дії: {} секунд').format(
                                                        response['data']['otp'], response['data']['timeRemaining']),
                                                    parse_mode='markdown')
                await state.set_data({'code_message_id': code_message.message_id})
            await asyncio.sleep(2)
        else:
            await message.answer(_('Неправильний ключ'))
            break

    state_data = await state.get_data()
    if 'code_message_id' in state_data:
        await message.bot.delete_message(chat_id=message.chat.id,
                                        message_id=state_data['code_message_id'])
