from typing import Any, Awaitable, Callable, Dict, List
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, TelegramObject
from loguru import logger
from bot.database import db, ChannelModel
from bot.keyboards.inline import get_subscription_keyboard
from bot.config import settings

async def check_user_subscriptions(bot: Bot, user_id: int, channels: List[ChannelModel]) -> List[ChannelModel]:
    """
    Returns list of channels that user is NOT yet subscribed to.
    """
    unsubscribed = []
    for ch in channels:
        chat_identifier = ch.username if ch.username else ch.link.split('/')[-1]
        if not chat_identifier.startswith('@') and not chat_identifier.startswith('-100') and not chat_identifier.isdigit():
            chat_identifier = f"@{chat_identifier}"

        try:
            member = await bot.get_chat_member(chat_id=chat_identifier, user_id=user_id)
            if member.status in ("left", "kicked"):
                unsubscribed.append(ch)
        except Exception as e:
            # If bot is not admin in channel or cannot check, log and don't block user unfairly
            logger.warning(f"Could not check membership for {chat_identifier} and user {user_id}: {e}")
    return unsubscribed

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        bot: Bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            text = event.text or ""
            # Don't intercept start commands or admin commands
            if text.startswith("/start") or text.startswith("/admin"):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            if event.data in ("check_subs",) or (event.data and event.data.startswith("adm_")):
                return await handler(event, data)

        if not user_id:
            return await handler(event, data)

        # Skip subscription check for admins
        if user_id in settings.admin_ids:
            return await handler(event, data)

        # Check channels
        channels = await db.get_active_channels()
        if channels:
            unsub = await check_user_subscriptions(bot, user_id, channels)
            if unsub:
                sub_text = "⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling:"
                kb = get_subscription_keyboard(unsub)
                if isinstance(event, Message):
                    await event.answer(sub_text, reply_markup=kb)
                elif isinstance(event, CallbackQuery):
                    await event.message.answer(sub_text, reply_markup=kb)
                    await event.answer()
                return

        return await handler(event, data)
