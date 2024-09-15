from aiogram.filters.callback_data import CallbackData


class EditAppsMenuCallback(CallbackData, prefix='user_apps'):
    action: str

class DeleteAppCallback(CallbackData, prefix='delete_app'):
    name: str
