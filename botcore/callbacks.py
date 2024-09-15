from aiogram.filters.callback_data import CallbackData


class EditAppsMenuCallback(CallbackData, prefix='user_apps'):
    action: str
