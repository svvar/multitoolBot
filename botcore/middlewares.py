from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

from .storage import get_lang


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
