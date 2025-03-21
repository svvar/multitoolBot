import re
import io

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.markdown import hbold
from aiogram.utils.i18n import lazy_gettext as __, gettext as _

from bot.core.states import CheckingInstAccounts
from bot.functions.inst_account_checking.instagram_manager import InstagramManager
from bot.core.usage_statistics import usage

inst_check_router = Router()

@inst_check_router.message(F.text == __('📷✅️ Перевірити Instagram на блокування'))
async def check(message: types.Message, state: FSMContext):
    back_kb = ReplyKeyboardBuilder()
    back_kb.button(text=_('🏠 В меню')).button(text=_('🔧🐞 Повідомити про помилку')).adjust(1)

    await message.answer(_('Введіть список username через кому або з нового рядка, або ж надішліть txt файл з username з нового рядка'),
                         reply_markup=back_kb.as_markup(resize_keyboard=True))
    await state.set_state(CheckingInstAccounts.entering_usernames)


@inst_check_router.message(CheckingInstAccounts.entering_usernames)
async def check_insta_acc(message: types.Message, state: FSMContext):
    back_kb = ReplyKeyboardBuilder()
    back_kb.button(text=_('🏠 В меню')).button(text=_('🔧🐞 Повідомити про помилку')).adjust(1)

    if message.document:
        if not message.document.file_name.endswith('.txt'):
            await message.answer(_('Неправильний формат файлу. Повторіть ввід'), reply_markup=back_kb.as_markup(resize_keyboard=True))
            return

        with io.BytesIO() as file:
            tg_file = await message.bot.get_file(message.document.file_id)
            await message.bot.download_file(tg_file.file_path, file)
            usernames = file.getvalue().decode('utf-8').splitlines()
        del file

        if not usernames:
            await message.answer(_('Файл порожній. Повторіть ввід'), reply_markup=back_kb.as_markup(resize_keyboard=True))
            return

        results = []
        insta_manager = InstagramManager()
        await insta_manager.init_shared()

        for username in usernames:
            if not validate_instagram_username(username):
                results.append(
                    {"username": username, "result": 'username містить не дозволені символи'})
                continue

            result = await insta_manager.check_acc(username)
            if result is None:
                results.append(
                    {"username": username, "result": _('Помилка при отриманні даних з інстаграм, спробуйте пізніше')})
            elif result is False:
                results.append({"username": username, "result": _('не знайдено або забанено')})
            else:
                results.append({"username": username, "result": _('активний')})

        with io.BytesIO() as file:
            file.name = 'check_results.txt'
            file.write("\n".join([f"{result['username']}  ->  {result['result']}" for result in results]).encode('utf-8'))
            file.seek(0)
            input_file = types.input_file.BufferedInputFile(file.getvalue(), filename=file.name)
            await message.answer_document(input_file)

        del file
        await state.clear()

    elif message.text:
        usernames = [username.strip() for username in re.split(r'[,\n]', message.text) if not username.isspace()]
        if not usernames:
            await message.answer(_('Формат вводу не розпізнано. Повторіть ввід'), reply_markup=back_kb.as_markup(resize_keyboard=True))
            return

        max_length = max(len(username) for username in usernames)

        response = []
        insta_manager = InstagramManager()
        await insta_manager.init_shared()

        for username in usernames:
            if not validate_instagram_username(username):
                response.append(
                    f"{hbold(username.ljust(max_length))} -> {_('username містить не дозволені символи')}")
                continue

            result = await insta_manager.check_acc(username)
            if result is None:
                response.append(
                    f"{hbold(username.ljust(max_length))} -> ⚠️ {_('Помилка при отриманні даних з інстаграм, спробуйте пізніше')}")
            elif result is False:
                response.append(
                    f"{hbold(username.ljust(max_length))} -> ❌ {_('не знайдено або забанено')}")
            else:
                response.append(
                    f"{hbold(username.ljust(max_length))} -> ✅ {_('активний')}")

        # Відправка результатів як текст
        await message.answer("\n".join(response), parse_mode='HTML', reply_markup=back_kb.as_markup(resize_keyboard=True))
        await state.clear()

    else:
        await message.answer(_('Неправильний формат файлу. Повторіть ввід'), reply_markup=back_kb.as_markup(resize_keyboard=True))
        return

    usage.inst_acc_check += 1


def validate_instagram_username(username: str) -> bool:
    if not (1 <= len(username) <= 30):
        return False

    regex = r"^[a-zA-Z0-9._]{1,30}$"
    if not re.match(regex, username):
        return False

    return True
