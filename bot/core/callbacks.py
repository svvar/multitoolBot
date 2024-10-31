from aiogram.filters.callback_data import CallbackData


class EditAppsMenuCallback(CallbackData, prefix='user_apps'):
    action: str


class CountryPageCallback(CallbackData, prefix='cntry_pg'):
    direction: str
    action: str