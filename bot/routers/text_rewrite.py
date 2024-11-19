import io

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import lazy_gettext as __, gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.core.states import TextRewrite
from bot.core.locale_helper import languages
from bot.core.storage import main_storage as storage
from bot.core.config import AI_API_TOKEN


rewrite_router = Router()

# GEMINI AI
genai.configure(api_key=AI_API_TOKEN)
model = genai.GenerativeModel(safety_settings="BLOCK_NONE", model_name="gemini-1.5-flash")


@rewrite_router.message(F.text == __('✍️ Перефразувати текст'))
async def rewrite_text(message: types.Message, state: FSMContext):
    await message.answer(_('Відправте текст, який потрібно перефразувати.'))
    await state.set_state(TextRewrite.entering_text)


def _settings_kb(
        translate: str = '❌',
        copies: int = 2,
        send_as: str = 'Telegram',
        generalization: int = 3,
        correct_mistakes: bool = True,
        emoji: bool = True,
        max_conversion: bool = False
):
    tweak_kb = InlineKeyboardBuilder()
    tweak_kb.button(text=f"{_('🌐 Перекласти')}: {translate}", callback_data='translate')
    tweak_kb.button(text=f"{_('🔄 Унікальних копій')}: {copies}", callback_data='copies')
    tweak_kb.button(text=f"{_('📤 Спосіб відправки')}: {send_as}", callback_data='send_as')
    # tweak_kb.button(text=f"{_('📄 Рівень узагальнення')}: {generalization}", callback_data='generalization')
    tweak_kb.button(text=f"{_('🛠️ Виправлення помилок')}: {_('Так') if correct_mistakes else _('Ні')}", callback_data='correct_mistakes')
    tweak_kb.button(text=f"{_('😀 Емоджі')}: {_('Так') if emoji else _('Ні')}", callback_data='emoji')
    tweak_kb.button(text=f"{_('📈 Змінити для максимізації конверсії')}: {_('Так') if max_conversion else _('Ні')}", callback_data='max_conversion')
    tweak_kb.button(text=_('Перефразувати'), callback_data='run')
    tweak_kb.adjust(1)

    return tweak_kb


def _lang_kb(locale: str):
    lang_kb = InlineKeyboardBuilder()
    lang_kb.button(text=_('❌ Не перекладати'), callback_data=f'❌')

    translated_lang = languages[locale]
    for lang_code, lang_name in translated_lang.items():
        lang_kb.button(text=f'{lang_name}', callback_data=lang_name)
    lang_kb.adjust(2)

    return lang_kb

@rewrite_router.message(TextRewrite.entering_text)
async def receive_text(message: types.Message, state: FSMContext):
    text = message.text

    kb = _settings_kb()

    tweak_msg = await message.answer(_('Налаштуйте кнопками нижче'), reply_markup=kb.as_markup())
    await state.set_state(TextRewrite.inline_menu)

    await state.update_data(text=text, translation='❌', copies=2, send_as='Telegram', generalization=3,
                            correct_mistakes=True, emoji=True, max_conversion=False, tweak_msg=tweak_msg.message_id)


async def start_tweak_kb(message: types.Message, state: FSMContext):
    data = await state.get_data()
    kb = _settings_kb(data['translation'], data['copies'], data['send_as'], data['generalization'],
                      data['correct_mistakes'], data['emoji'], data['max_conversion'])

    tweak_msg = await message.answer(_('Налаштуйте кнопками нижче'), reply_markup=kb.as_markup())
    await state.set_state(TextRewrite.inline_menu)
    await state.update_data(tweak_msg=tweak_msg.message_id)


async def update_tweak_kb(message: types.Message, state: FSMContext):
    data = await state.get_data()
    translation = data['translation']
    copies = data['copies']
    send_as = data['send_as']
    generalization = data['generalization']
    correct_mistakes = data['correct_mistakes']
    emoji = data['emoji']
    max_conversion = data['max_conversion']
    tweak_msg = data['tweak_msg']

    kb = _settings_kb(translation, copies, send_as, generalization, correct_mistakes, emoji, max_conversion)

    try:
        await message.bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=tweak_msg, reply_markup=kb.as_markup())
    except Exception as e:
        print(e)

    await state.set_state(TextRewrite.inline_menu)


@rewrite_router.callback_query(TextRewrite.inline_menu)
async def tweaking(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if callback.data == 'translate':
        user_locale = await storage.get_lang(callback.from_user.id)
        kb = _lang_kb(user_locale)
        await callback.message.answer(_('Оберіть мову перекладу:'), reply_markup=kb.as_markup())
        await state.set_state(TextRewrite.selecting_lang)
        await callback.answer()
        return
    elif callback.data == 'copies':
        await callback.message.answer(_('Введіть значення від {} до {}:').format(1, 10))
        await state.set_state(TextRewrite.entering_copies)
        await callback.answer()
        return
    elif callback.data == 'send_as':
        data['send_as'] = 'TXT' if data['send_as'] == 'Telegram' else 'Telegram'
    # elif callback.data == 'generalization':
    #     await callback.message.answer(_('Введіть значення від {} до {}:').format(1, 10))
    #     await state.set_state(TextRewrite.entering_generalization)
    #     await callback.answer()
    #     return
    elif callback.data == 'correct_mistakes':
        data['correct_mistakes'] = not data['correct_mistakes']
    elif callback.data == 'emoji':
        data['emoji'] = not data['emoji']
    elif callback.data == 'max_conversion':
        data['max_conversion'] = not data['max_conversion']
    elif callback.data == 'run':
        await callback.answer()
        await callback.message.answer(_('Зачекайте, текст обробляється...'))
        await run_with_ai(callback.message, state)
        return

    await state.update_data(data)
    await callback.answer()
    await update_tweak_kb(callback.message, state)


@rewrite_router.callback_query(TextRewrite.selecting_lang)
async def set_language(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data

    await callback.answer()
    await state.update_data(translation=lang)
    await callback.message.delete()
    await update_tweak_kb(callback.message, state)


@rewrite_router.message(TextRewrite.entering_copies)
# @rewrite_router.message(TextRewrite.entering_generalization)
async def entering_value(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
    except ValueError:
        await message.answer(_('Введіть число!'))
        return

    state_name = await state.get_state()
    if state_name == TextRewrite.entering_copies:
        if 1 <= value <= 10:
            await state.update_data(copies=value)
        else:
            await message.answer(_('Введіть число від {} до {}:').format(1, 10))
            return
    # elif state_name == TextRewrite.entering_generalization:
    #     if 1 <= value <= 10:
    #         await state.update_data(generalization=value)
    #     else:
    #         await message.answer(_('Введіть число від {} до {}:').format(1, 10))
    #         return

    data = await state.get_data()
    await message.bot.delete_message(chat_id=message.chat.id, message_id=data['tweak_msg'])
    await start_tweak_kb(message, state)


async def run_with_ai(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = data['text']
    translation = data['translation']
    copies = data['copies']
    send_as = data['send_as']
    generalization = data['generalization']
    correct_mistakes = data['correct_mistakes']
    emoji = data['emoji']
    max_conversion = data['max_conversion']

    await state.clear()
    #
    # prompt = (f'INSTRUCTIONS:\n'
    #           f'Lower you\'ll get text, here is what you need to do with that text:\n'
    #           f'{("Translate to " + translation) if translation != "❌" else ""}\n'
    #           f'{"Generalize text (1 - minimum generalization, 10 - maximum). Level: " + str(generalization)}\n'
    #           f'Higher Generalization means that the text will be more abstract and less specific.\n'
    #           f'{"Correct mistakes. " if correct_mistakes else "Do not correct mistakes"}'
    #           f'{"Use emoji. " if emoji else "Do not use emoji"}'
    #           f'{"Change text to maximize leads conversion (advert). " if max_conversion else ""}'
    #           f'{"Finally, generate " + str(copies) + " unique copies (variants of text) with these settings" if copies > 1 else ""}'
    #           f'Separate each copy with "+-+" sequence. Do not add anything else to the text (headers, explanations, etc.)\n'
    #           f'\nTEXT:\n{text}')
    #
    # input = {
    #     "prompt": prompt,
    #     "system_prompt": "You are a helper of a content creator and you need to modify the text making listed changes. Instructions are written in English, but Text can be in any language, you should translate it only if there is such instruction.",
    #     "max_new_tokens": 5000,
    # }

    prompt = (f'ІНСТРУКЦІЇ:\n'
              f'Нижче ти побачиш текст, ось що потрібно зробити з цим текстом:\n'
              f'{("Перекласти на " + translation) if translation != "❌" else ""}\n'
              f'Перефразуй текст, зберігай важливі дані (контакти, посилання абощо). Об\'єм тексту збережи приблизно таким же\n'
              f'{"Виправи помилки якщо є. " if correct_mistakes else "Не виправляй помилки"}\n'
              f'{"Використовуй емодзі. " if emoji else "Не використовуй емодзі"}\n'
              f'{"Зміни текст для максимізації конверсії лідів (для реклами). " if max_conversion else ""}'
              f'{"Створи " + str(copies) + " унікальних копій (варіантів тексту) з цими налаштуваннями"}'
              f'Відокремлюй кожну копію послідовністю "+-+-+-+-+-+-+-+". Не додавай нічого іншого до тексту (заголовки, пояснення тощо).\n'
              f'\nТЕКСТ:\n{text}')

    # input = {
    #     "prompt": prompt,
    #     "system_prompt": "Ти помічник творця контенту і тобі потрібно змінити текст, внесши перелічені зміни. "
    #                      "Текст може бути будь-якою мовою, ви повинні перекласти його тільки якщо є така інструкція.",
    #     "max_new_tokens": 5000,
    # }
    #
    # response = await ai_client.async_run(
    #     "meta/meta-llama-3-70b-instruct",
    #     input=input,
    #     use_file_output=False
    # )
    # response = ''.join(response)

    try:
        response = await model.generate_content_async(prompt)
        response_msg = response.text
    except ResourceExhausted:
        await message.answer(_('Забагато запитів від користувачів, спробуйте за хвилину'))
        return

    if len(response_msg) <= 4096 and send_as == 'Telegram':
        await message.answer(response_msg)

    elif len(response_msg) > 4096 and send_as == 'Telegram':
        for i in range(0, len(response_msg), 4096):
            await message.answer(response_msg[i:i + 4096])

    elif send_as == 'TXT':
        with io.BytesIO() as file:
            file.name = 'text_variants.txt'
            file.write(response_msg.encode('utf-8'))
            input_file = types.input_file.BufferedInputFile(file.getvalue(), filename=file.name)
            await message.answer_document(input_file)


