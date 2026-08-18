from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from bot.database import db
from bot.keyboards.inline import get_referral_keyboard
from bot.config import settings

referral_router = Router(name="referral_router")

@referral_router.message(F.text.in_(["🧑‍💼 Pul ishlash", "🧑💼 Pul ishlash", "🐥 Pul ishlash", "🙋 Pul ishlash", "Pul ishlash"]))
async def handle_pul_ishlash(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        user, _ = await db.create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    bot_user = settings.BOT_USERNAME.lstrip("@")
    ref_link = f"https://t.me/{bot_user}?start=user{user_id}"

    text = (
        "🔗 <b>Sizning referal havolangiz:</b>\n\n"
        f"{ref_link}\n\n"
        f"<i>Sizga har bir taklif qilgan referalingiz uchun {settings.REFERRAL_REWARD} so'm beriladi.</i>\n\n"
        f"🐥 <b>ID raqam: {user.telegram_id}</b>\n\n"
        "Telegram\n"
        "<b>Turfa Seen | Rasmiy</b>\n"
        f"Rasmiy kanalimiz : {settings.OFFICIAL_CHANNEL}\n"
        f"Admin : {settings.SUPPORT_ADMIN}\n"
        f"💠 {settings.WEBSITE_URL}"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=get_referral_keyboard())

@referral_router.callback_query(F.data == "ref_top10")
async def callback_top10_referrals(callback: CallbackQuery):
    top_users = await db.get_top_referrers(limit=10)

    lines = ["🏆 <b>Eng ko'p do'st taklif qilgan TOP 10 foydalanuvchilar:</b>\n"]
    if not top_users:
        lines.append("Hozircha referallar mavjud emas.")
    else:
        for idx, u in enumerate(top_users, start=1):
            name = u.first_name or f"ID: {u.telegram_id}"
            count = u.referral_count
            lines.append(f"<b>{idx}.</b> {name} — <b>{count} ta</b> referal")

    await callback.message.answer("\n".join(lines), parse_mode="HTML")
    await callback.answer()
