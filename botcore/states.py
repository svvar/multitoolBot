from aiogram.fsm.state import State, StatesGroup

class CheckingAccounts(StatesGroup):
    start_checking = State()
    file_input = State()
    message_input = State()