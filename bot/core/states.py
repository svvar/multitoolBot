from aiogram.fsm.state import State, StatesGroup

class Setup(StatesGroup):
    choosing_lang = State()

class CheckingAccounts(StatesGroup):
    start_checking = State()
    file_input = State()
    message_input = State()

class CheckingInstAccounts(StatesGroup):
    entering_usernames = State()

class TwoFA(StatesGroup):
    key_input_msg = State()
    key_input_callback = State()
    fetching_data = State()

class TikTokDownload(StatesGroup):
    url_input = State()

class Apps(StatesGroup):
    info_shown = State()
    entering_url = State()
    selecting_to_delete = State()

class IdGenerator(StatesGroup):
    need_meta = State()
    selecting_photo = State()
    selecting_color = State()
    selecting_sex = State()
    entering_name = State()
    entering_age = State()
    generating = State()


class Uniquilizer(StatesGroup):
    media_input = State()
    copies_num = State()
    generating = State()


class AdminMailing(StatesGroup):
    selecting_lang = State()
    entering_message = State()
    asking_links = State()
    preview = State()
    process = State()

class AdminWelcome(StatesGroup):
    entering_message = State()
    entering_links = State()
    saving = State()


class PasswordGen(StatesGroup):
    tweaking = State()
    changing_chars = State()
    changing_amount = State()


class NameGen(StatesGroup):
    selecting_gender = State()
    selecting_country = State()

class FanPageName(StatesGroup):
    entering_amount = State()

class AddressGen(StatesGroup):
    selecting_country = State()
    entering_amount = State()

class PhoneGen(StatesGroup):
    selecting_country = State()
    entering_amount = State()

class QuoteGen(StatesGroup):
    selecting_country = State()
    entering_amount = State()

class AllFanPageGen(StatesGroup):
    selecting_country = State()
    entering_amount = State()


class SelfieGen(StatesGroup):
    selecting_gender = State()
    selecting_age = State()


class TextRewrite(StatesGroup):
    entering_text = State()
    inline_menu = State()
    selecting_lang = State()
    entering_copies = State()
    entering_generalization = State()

class BugReport(StatesGroup):
    describing_bug = State()
    dev_entering_reply = State()