import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            current_time = time.time()
            last_time = self.user_timestamps.get(user_id, 0)
            if current_time - last_time < self.rate_limit:
                # Anti-flood hit
                if isinstance(event, Message):
                    await event.answer("⚠️ Iltimos, juda tez xabar yubormang!")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⚠️ Iltimos, biroz kuting!", show_alert=False)
                return
            self.user_timestamps[user_id] = current_time

        return await handler(event, data)
