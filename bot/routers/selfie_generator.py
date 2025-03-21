import random
import os


from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot.core.usage_statistics import usage
from bot.core.states import SelfieGen


selfie_gen_router = Router()


@selfie_gen_router.message(F.text == __('🤳 Генератор селфі'))
async def selfie_start(message: types.Message, state: FSMContext):

    kb = ReplyKeyboardBuilder()
    kb.button(text=_('🕺 Чоловіча'))
    kb.button(text=_('💃 Жіноча'))
    kb.button(text=_('🏠 В меню'))
    kb.button(text=_('🔧🐞 Повідомити про помилку'))
    kb.adjust(1)

    await message.answer(_('Виберіть стать:'), reply_markup=kb.as_markup(resize_keyboard=True))
    await state.set_state(SelfieGen.selecting_gender)


@selfie_gen_router.message(SelfieGen.selecting_gender)
async def selfie_age(message: types.Message, state: FSMContext):
    if message.text == _('🕺 Чоловіча'):
        await state.update_data(sex='male')
    elif message.text == _('💃 Жіноча'):
        await state.update_data(sex='female')
    else:
        await message.answer(_('Некоректне значення, введіть ще раз'))


    kb = ReplyKeyboardBuilder()
    kb.button(text=_('👶 Молодий'))
    kb.button(text=_('🧑 Середній'))
    kb.button(text=_('👴 Старший'))
    kb.button(text=_('🏠 В меню'))
    kb.button(text=_('🔧🐞 Повідомити про помилку'))
    kb.adjust(3)

    await message.answer(_('Виберіть бажаний вік:\n(намагатиметься згенерувати фото з вибраним віком)'),
                         reply_markup=kb.as_markup(resize_keyboard=True))
    await state.set_state(SelfieGen.selecting_age)


@selfie_gen_router.message(SelfieGen.selecting_age)
async def selfie_gen_state(message: types.Message, state: FSMContext):
    age = message.text
    if age == _('👶 Молодий'):
        age = 'young'
    elif age == _('🧑 Середній'):
        age = 'middle'
    elif age == _('👴 Старший'):
        age = 'old'
    else:
        await message.answer(_('Некоректне значення, введіть ще раз'))
        return

    state_data = await state.get_data()
    sex = state_data['sex']

    input_file = _selfie_get_file(sex, age)

    kb = InlineKeyboardBuilder()
    kb.button(text=_('🔄 Ще одне селфі'), callback_data=f'selfie_{sex}_{age}')

    await message.answer_photo(input_file, reply_markup=kb.as_markup())
    usage.selfie_generator += 1


@selfie_gen_router.callback_query(F.data.startswith('selfie'))
async def selfie_gen_callback(callback: types.CallbackQuery):
    data = callback.data.split('_')
    sex = data[1]
    age = data[2]

    input_file = _selfie_get_file(sex, age)
    kb = InlineKeyboardBuilder()
    kb.button(text=_('🔄 Ще одне селфі'), callback_data=callback.data)

    await callback.answer()
    await callback.message.answer_photo(input_file, reply_markup=kb.as_markup())

    # usage['selfie_generator'] += 1


def _selfie_get_file(sex, age):
    path = f'./assets/selfieGenerator/{sex}/'
    if age == 'young':
        path += random.choice(['20-24', '25-29'])
    elif age == 'middle':
        path += random.choice(['30-34', '35-39'])
    elif age == 'old':
        path += random.choice(['40-44', '45-49', '50+'])

    file = random.choice(os.listdir(path))
    return types.FSInputFile(f'{path}/{file}')