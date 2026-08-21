from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards.reply import get_main_menu_keyboard
from bot.keyboards.inline import get_raqam_olish_keyboard
from bot.config import settings
from bot.services import settings_service

main_menu_router = Router(name="main_menu_router")

@main_menu_router.message(F.text.in_(["📞 Raqam olish", "Raqam olish"]))
async def handle_raqam_olish(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "🤗 <b>Telegram uchun tayyor hisoblar:</b>\n\n"
        "Tez orada avtomatik tarzda qo'shiladi.\n"
        "🛒 Agar sizga hoziroq spam bo'lmagan ishonchli hisob kerak bo'lsa, admin orqali xarid qilishingiz mumkin."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_raqam_olish_keyboard())

@main_menu_router.message(F.text.in_(["? Yordam", "🔨 Yordam", "❓ Yordam", "Yordam"]))
async def handle_yordam(message: Message, state: FSMContext):
    await state.clear()
    support_admin = settings_service.get_support_admin()
    text = (
        "❓ <b>Yordam va qo'llab-quvvatlash</b>\n\n"
        "Bot yordamida ijtimoiy tarmoqlaringizni tez va sifatli rivojlantirishingiz mumkin.\n\n"
        f"👤 Admin: {support_admin}\n"
        f"📢 Rasmiy kanal: {settings.OFFICIAL_CHANNEL}\n"
        f"💎 Saytimiz: {settings.WEBSITE_URL}\n\n"
        "Muammolar yoki takliflar bo'lsa, adminga yozishingiz mumkin."
    )
    await message.answer(text, parse_mode="HTML")

@main_menu_router.message(F.text.in_(["💻 Hamkorlik dasturi", "📚 Hamkorlik dasturi", "Hamkorlik dasturi"]))
async def handle_hamkorlik(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "📚 <b>Hamkorlik dasturi (Referal tizimi)</b>\n\n"
        "Do'stlaringizni botimizga taklif qilib, qo'shimcha daromad oling!\n\n"
        f"💵 Har bir taklif qilingan foydalanuvchi uchun: <b>{settings.REFERRAL_REWARD} so'm</b> beriladi.\n"
        "To'plangan mablag'larni botdagi istalgan xizmatlar uchun sarflashingiz mumkin.\n\n"
        "Taklif havolangizni olish uchun <b>'🧑‍💼 Pul ishlash'</b> tugmasini bosing."
    )
    await message.answer(text, parse_mode="HTML")

@main_menu_router.message(Command("cancel"))
@main_menu_router.message(F.text.in_(["❌ Bekor qilish", "Bekor qilish", "❌ Chiqish", "Chiqish", "/cancel"]))
async def handle_cancel_reply(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.\n\n📩 Asosiy menyudasiz", reply_markup=get_main_menu_keyboard())

@main_menu_router.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("📩 Asosiy menyudasiz", reply_markup=get_main_menu_keyboard())
    await callback.answer()
