from aiogram import Router, Bot, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from loguru import logger
from bot.database import db
from bot.keyboards.reply import get_main_menu_keyboard
from bot.keyboards.inline import get_subscription_keyboard
from bot.middlewares.subscription_check import check_user_subscriptions
from bot.config import settings

start_router = Router(name="start_router")

@start_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Parse referral parameter (e.g. user15636 or 15636)
    referrer_id = None
    if command.args:
        arg = command.args.strip()
        if arg.startswith("user"):
            ref_str = arg[4:]
            if ref_str.isdigit():
                referrer_id = int(ref_str)
        elif arg.isdigit():
            referrer_id = int(arg)

    # Prevent self-referral
    if referrer_id == user_id:
        referrer_id = None

    user, is_new = await db.create_or_get_user(
        telegram_id=user_id,
        username=username,
        first_name=first_name,
        referrer_id=referrer_id
    )

    # If new user and referrer exists, reward referrer
    if is_new and referrer_id:
        rewarded = await db.add_referral_reward(referrer_id=referrer_id, referred_id=user_id, reward=settings.REFERRAL_REWARD)
        if rewarded:
            try:
                await bot.send_message(
                    chat_id=referrer_id,
                    text="🎉 <b>Sizda yangi referal!</b>\nHisobingizga 80 so'm qo'shildi.",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Could not notify referrer {referrer_id}: {e}")

    # Check subscriptions
    channels = await db.get_active_channels()
    if channels and user_id not in settings.admin_ids:
        unsub = await check_user_subscriptions(bot, user_id, channels)
        if unsub:
            await message.answer(
                "⚠️ Botdan foydalanish uchun, quyidagi kanallarga obuna bo'ling:",
                reply_markup=get_subscription_keyboard(unsub)
            )
            return

    # Show Main Menu
    await message.answer(
        "📩 Asosiy menyudasiz",
        reply_markup=get_main_menu_keyboard()
    )

@start_router.callback_query(F.data == "check_subs")
async def callback_check_subs(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    channels = await db.get_active_channels()
    if channels and user_id not in settings.admin_ids:
        unsub = await check_user_subscriptions(bot, user_id, channels)
        if unsub:
            await callback.answer("⚠️ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
            await callback.message.edit_reply_markup(reply_markup=get_subscription_keyboard(unsub))
            return

    await callback.answer("✅ Obuna tasdiqlandi!")
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("📩 Asosiy menyudasiz", reply_markup=get_main_menu_keyboard())
