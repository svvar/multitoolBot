from aiogram.fsm.state import State, StatesGroup

class Setup(StatesGroup):
    choosing_lang = State()

class CheckingAccounts(StatesGroup):
    start_checking = State()
    file_input = State()
    message_input = State()

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
