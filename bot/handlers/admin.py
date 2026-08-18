from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from loguru import logger
from bot.database import db
from bot.config import settings
from bot.states import AdminStates
from bot.keyboards.inline import get_admin_main_keyboard

admin_router = Router(name="admin_router")

def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids

# --- /admin COMMAND ---

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    stats = await db.get_admin_stats()
    text = (
        "👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"🛒 Jami buyurtmalar: <b>{stats['total_orders']}</b>\n"
        f"⏳ Kutilayotgan to'lovlar: <b>{stats['pending_payments']}</b>\n\n"
        "Tezkor buyruq: <code>/add_balance USER_ID AMOUNT</code>"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_keyboard())

# --- /add_balance COMMAND ---

@admin_router.message(Command("add_balance"))
async def cmd_add_balance(message: Message, command: CommandObject, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    if not command.args:
        await message.answer("⚠️ Format: <code>/add_balance USER_ID AMOUNT</code>\nMasalan: <code>/add_balance 8048583227 10000</code>", parse_mode="HTML")
        return

    parts = command.args.split()
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await message.answer("⚠️ Foydalanuvchi ID va summa butun son bo'lishi kerak!")
        return

    target_id = int(parts[0])
    amount = int(parts[1])

    success = await db.update_balance(target_id, amount, is_deposit=True)
    if success:
        amount_fmt = f"{amount:,}".replace(",", " ")
        await message.answer(f"✅ Foydalanuvchi <code>{target_id}</code> hisobiga <b>{amount_fmt} so'm</b> muvaffaqiyatli qo'shildi!", parse_mode="HTML")
        try:
            await bot.send_message(
                chat_id=target_id,
                text=f"💳 <b>Hisobingiz to'ldirildi!</b>\n\nBalansingizga <b>+{amount_fmt} so'm</b> qo'shildi. Xaridingiz uchun rahmat!",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Could not notify user {target_id}: {e}")
    else:
        await message.answer(f"❌ Foydalanuvchi {target_id} topilmadi yoki xatolik yuz berdi.")

# --- ADMIN CALLBACKS ---

@admin_router.callback_query(F.data == "adm_stats")
async def callback_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    stats = await db.get_admin_stats()
    text = (
        "📊 <b>Batafsil Statistika:</b>\n\n"
        f"👥 Foydalanuvchilar soni: <b>{stats['total_users']} ta</b>\n"
        f"📦 Buyurtmalar soni: <b>{stats['total_orders']} ta</b>\n"
        f"💳 Kutilayotgan to'lov cheklari: <b>{stats['pending_payments']} ta</b>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_main_keyboard())
    await callback.answer()

@admin_router.callback_query(F.data == "adm_channels")
async def callback_admin_channels(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    channels = await db.get_active_channels()
    lines = ["📢 <b>Majburiy a'zolik kanallari:</b>\n"]
    for ch in channels:
        lines.append(f"• <b>{ch.name}</b> ({ch.link})")

    await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=get_admin_main_keyboard())
    await callback.answer()

@admin_router.callback_query(F.data == "adm_add_bal")
async def callback_admin_add_bal_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_add_balance_user_id)
    await callback.message.answer("✍️ Balans qo'shmoqchi bo'lgan foydalanuvchining <b>Telegram ID</b>sini yuboring:", parse_mode="HTML")
    await callback.answer()

@admin_router.message(AdminStates.waiting_for_add_balance_user_id)
async def process_admin_target_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamli Telegram ID kiriting:")
        return

    await state.update_data(target_user_id=int(text))
    await state.set_state(AdminStates.waiting_for_add_balance_amount)
    await message.answer(f"💰 Foydalanuvchi (ID: {text}) uchun qo'shiladigan <b>summani (so'mda)</b> kiriting:", parse_mode="HTML")

@admin_router.message(AdminStates.waiting_for_add_balance_amount)
async def process_admin_target_amount(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat musbat son kiriting:")
        return

    amount = int(text)
    data = await state.get_data()
    target_id = data.get("target_user_id")

    success = await db.update_balance(target_id, amount, is_deposit=True)
    await state.clear()

    if success:
        amount_fmt = f"{amount:,}".replace(",", " ")
        await message.answer(f"✅ Foydalanuvchi <code>{target_id}</code> hisobiga <b>{amount_fmt} so'm</b> qo'shildi!", parse_mode="HTML")
        try:
            await bot.send_message(
                chat_id=target_id,
                text=f"💳 <b>Hisobingiz to'ldirildi!</b>\n\nBalansingizga <b>+{amount_fmt} so'm</b> qo'shildi.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Could not notify user {target_id}: {e}")
    else:
        await message.answer(f"❌ Foydalanuvchi {target_id} topilmadi.")

# --- PAYMENT APPROVE / REJECT FROM PHOTO BUTTONS ---

@admin_router.callback_query(F.data.startswith("adm_pay_appr_"))
async def callback_approve_payment_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    parts = callback.data.split("_")
    payment_id = int(parts[3])
    user_id = int(parts[4])

    await state.set_state(AdminStates.waiting_for_payment_approve_amount)
    await state.update_data(payment_id=payment_id, user_id=user_id)

    quick_amounts_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5 000 so'm", callback_data=f"adm_set_amt_{payment_id}_{user_id}_5000", style="primary"),
            InlineKeyboardButton(text="10 000 so'm", callback_data=f"adm_set_amt_{payment_id}_{user_id}_10000", style="primary"),
        ],
        [
            InlineKeyboardButton(text="20 000 so'm", callback_data=f"adm_set_amt_{payment_id}_{user_id}_20000", style="primary"),
            InlineKeyboardButton(text="50 000 so'm", callback_data=f"adm_set_amt_{payment_id}_{user_id}_50000", style="primary"),
        ],
        [
            InlineKeyboardButton(text="100 000 so'm", callback_data=f"adm_set_amt_{payment_id}_{user_id}_100000", style="primary"),
        ]
    ])

    await callback.message.reply(
        f"💰 To'lov #{payment_id} uchun summani tanlang yoki xabar sifatida yozing:",
        reply_markup=quick_amounts_kb
    )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("adm_set_amt_"))
async def callback_set_payment_amount_quick(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    parts = callback.data.split("_")
    payment_id = int(parts[3])
    user_id = int(parts[4])
    amount = int(parts[5])

    await db.update_payment_status(payment_id, status="Approved", amount=amount)
    await db.update_balance(user_id, amount, is_deposit=True)
    await state.clear()

    amount_fmt = f"{amount:,}".replace(",", " ")
    await callback.message.edit_text(f"✅ To'lov #{payment_id} tasdiqlandi. Foydalanuvchi ({user_id}) hisobiga <b>{amount_fmt} so'm</b> qo'shildi!", parse_mode="HTML")
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 <b>To'lovingiz tasdiqlandi!</b>\n\nHisobingizga <b>+{amount_fmt} so'm</b> qo'shildi. Botdan unumli foydalaning!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Could not notify user {user_id}: {e}")
    await callback.answer()

@admin_router.message(AdminStates.waiting_for_payment_approve_amount)
async def process_payment_custom_amount(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, to'g'ri musbat son kiriting:")
        return

    amount = int(text)
    data = await state.get_data()
    payment_id = data.get("payment_id")
    user_id = data.get("user_id")

    await db.update_payment_status(payment_id, status="Approved", amount=amount)
    await db.update_balance(user_id, amount, is_deposit=True)
    await state.clear()

    amount_fmt = f"{amount:,}".replace(",", " ")
    await message.answer(f"✅ To'lov #{payment_id} tasdiqlandi! Foydalanuvchi ({user_id}) ga <b>{amount_fmt} so'm</b> qo'shildi.", parse_mode="HTML")

    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 <b>To'lovingiz tasdiqlandi!</b>\n\nHisobingizga <b>+{amount_fmt} so'm</b> qo'shildi.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Could not notify user {user_id}: {e}")

@admin_router.callback_query(F.data.startswith("adm_pay_rej_"))
async def callback_reject_payment(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    parts = callback.data.split("_")
    payment_id = int(parts[3])
    user_id = int(parts[4])

    await db.update_payment_status(payment_id, status="Rejected")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.reply(f"❌ To'lov #{payment_id} rad etildi.")

    try:
        await bot.send_message(
            chat_id=user_id,
            text="❌ <b>To'lov chekingiz rad etildi!</b>\n\nChekda ma'lumotlar to'liq emas yoki to'lov amalga oshirilmagan. Savollar bo'lsa adminga murojaat qiling.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Could not notify user {user_id}: {e}")
    await callback.answer()
