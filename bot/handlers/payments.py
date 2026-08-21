from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger
from bot.database import db, PaymentModel
from bot.keyboards.reply import get_main_menu_keyboard, get_cancel_keyboard
from bot.keyboards.inline import (
    get_hisobim_keyboard,
    get_payment_systems_keyboard,
    get_payment_detail_keyboard,
    get_admin_payment_keyboard
)
from bot.states import PaymentStates
from bot.config import settings
from bot.services import settings_service

payments_router = Router(name="payments_router")

# --- HISOBIM ---

@payments_router.message(F.text.in_(["💎 Hisobim", "Hisobim"]))
async def handle_hisobim(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        user, _ = await db.create_or_get_user(user_id, message.from_user.username, message.from_user.first_name)

    balance_fmt = f"{user.balance:,}".replace(",", " ")
    deposit_fmt = f"{user.total_deposit:,}".replace(",", " ")

    text = (
        f"👤 <b>Hisobingiz:</b> {balance_fmt} so'm\n"
        f"💎 <b>Kiritgan pullaringiz:</b> {deposit_fmt} so'm\n"
        f"🔔 <b>ID:</b> <code>{user.telegram_id}</code>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_hisobim_keyboard())

# --- PUL KIRITISH ---

@payments_router.message(F.text.in_(["💳 Pul kiritish", "Pul kiritish"]))
@payments_router.callback_query(F.data == "deposit_money")
async def handle_pul_kiritish(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "💳 <b>Hisobni to'ldirish</b>\n\n"
        "Kerakli to'lov tizimini tanlang:"
    )
    kb = get_payment_systems_keyboard()

    if isinstance(event, Message):
        await event.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        try:
            await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            await event.message.answer(text, parse_mode="HTML", reply_markup=kb)
        await event.answer()

@payments_router.callback_query(F.data.startswith("pay_"))
async def callback_payment_system_selected(callback: CallbackQuery):
    system = callback.data.split("_")[1]
    card_number = settings_service.get_card_number()
    comment = settings_service.get_card_comment()

    text = (
        f"💳 <b>To'lov tizimi:</b> {system}\n"
        f"💳 <b>Hamyon / Karta:</b> <code>{card_number}</code>\n"
        f"➡️ <b>Izoh (Karta egasi):</b> <code>{comment}</code>\n\n"
        "📸 <i>To'lovni amalga oshirgach, to'lov chekini skrinshot tarzda nusxa olib botga yuboring.</i>\n"
        "<i>E'tiborli bo'ling, chekda sana va tranzaksiya ma'lumoti aniq ko'rinsin.</i>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_payment_detail_keyboard(system)
    )
    await callback.answer()

@payments_router.callback_query(F.data.startswith("paid_"))
async def callback_paid_button(callback: CallbackQuery, state: FSMContext):
    system = callback.data.split("_")[1]
    await state.set_state(PaymentStates.waiting_for_screenshot)
    await state.update_data(payment_system=system)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"📸 <b>{system}</b> orqali to'lov qilingan chek skrinshotini (rasmini) yuboring:\n\n"
        "<i>Bekor qilish uchun '❌ Bekor qilish' tugmasini bosing.</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@payments_router.message(PaymentStates.waiting_for_screenshot, F.photo)
async def process_payment_screenshot(message: Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1]
    file_id = photo.file_id

    data = await state.get_data()
    system = data.get("payment_system", "CLICK")
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    username = f"@{message.from_user.username}" if message.from_user.username else "mavjud emas"
    card_number = settings_service.get_card_number()
    comment = settings_service.get_card_comment()

    # Save payment to DB
    payment = PaymentModel(
        user_telegram_id=user_id,
        system=system,
        card_number=card_number,
        comment=comment,
        screenshot_file_id=file_id,
        status="Pending"
    )
    saved_payment = await db.create_payment(payment)
    payment_id = saved_payment.id if saved_payment else 1

    await state.clear()

    # Reply to user
    await message.answer(
        "✅ <b>To'lov chekingiz qabul qilindi!</b>\n\n"
        "Adminlarimiz to'lovni tez orada tekshirib, hisobingizga mablag'ni qo'shib berishadi. Kuting.",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )

    # Forward to Admins
    admin_caption = (
        "💳 <b>Yangi to'lov cheki!</b>\n\n"
        f"👤 Foydalanuvchi: {first_name} ({username})\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"💳 Tizim: <b>{system}</b>\n"
        f"🔢 To'lov ID: <b>#{payment_id}</b>"
    )

    for admin_id in settings.admin_ids:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=file_id,
                caption=admin_caption,
                parse_mode="HTML",
                reply_markup=get_admin_payment_keyboard(payment_id, user_id)
            )
        except Exception as e:
            logger.error(f"Error sending payment screenshot to admin {admin_id}: {e}")

@payments_router.message(PaymentStates.waiting_for_screenshot, F.text.in_(["❌ Bekor qilish", "/cancel", "Bekor qilish", "❌ Chiqish", "Chiqish"]))
async def cancel_payment_upload(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ To'lov bekor qilindi.\n\n📩 Asosiy menyudasiz", reply_markup=get_main_menu_keyboard())

@payments_router.message(PaymentStates.waiting_for_screenshot)
async def invalid_payment_upload(message: Message):
    await message.answer("⚠️ Iltimos, to'lov chekini faqat <b>rasm (skrinshot)</b> ko'rinishida yuboring yoki bekor qilish uchun '❌ Bekor qilish' ni bosing:", parse_mode="HTML", reply_markup=get_cancel_keyboard())
