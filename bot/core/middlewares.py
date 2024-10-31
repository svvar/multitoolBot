from typing import Callable, Dict, Any, Awaitable, Optional
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, User
from aiogram.utils.i18n.middleware import I18nMiddleware

from bot.core.storage.main_storage import get_lang

try:
    from babel import Locale, UnknownLocaleError
except ImportError:  # pragma: no cover
    Locale = None  # type: ignore

    class UnknownLocaleError(Exception):  # type: ignore
        pass

class LangMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        event_chat = data['event_chat']
        user_id = event_chat.id

        lang = await get_lang(user_id)

        data['lang'] = lang
        return await handler(event, data)



class DatabaseI18nMiddleware(I18nMiddleware):
    def __init__(
            self,
            i18n,
            i18n_key="i18n",
            middleware_key="i18n_middleware"
    ):
        super().__init__(i18n, i18n_key, middleware_key)

    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        event_from_user: Optional[User] = data.get("event_from_user", None)

        user_id = event_from_user.id
        lang = await get_lang(user_id)

        return lang
