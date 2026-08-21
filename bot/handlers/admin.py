from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from loguru import logger
from bot.database import db
from bot.config import settings
from bot.states import AdminStates
from bot.services import settings_service, admin_service
from bot.keyboards.reply import get_main_menu_keyboard, get_cancel_keyboard
from bot.keyboards.inline import (
    get_admin_main_keyboard,
    get_admin_card_keyboard,
    get_admin_start_msg_keyboard
)

admin_router = Router(name="admin_router")

def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids

# --- /admin COMMAND ---

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    stats = await db.get_admin_stats()
    text = (
        "👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b> ta\n"
        f"🛒 Jami buyurtmalar: <b>{stats['total_orders']}</b> ta\n"
        f"⏳ Kutilayotgan to'lovlar: <b>{stats['pending_payments']}</b> ta\n\n"
        f"💳 <b>Hozirgi karta:</b> <code>{settings_service.get_card_number()}</code>\n"
        f"👤 <b>Izoh / Karta egasi:</b> <code>{settings_service.get_card_comment()}</code>\n\n"
        "<i>Quyidagi bo'limlardan birini tanlang:</i>"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_keyboard())

# --- ADMIN MAIN MENU CALLBACKS ---

@admin_router.callback_query(F.data == "adm_back_to_main")
async def callback_admin_back_to_main(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.clear()
    stats = await db.get_admin_stats()
    text = (
        "👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b> ta\n"
        f"🛒 Jami buyurtmalar: <b>{stats['total_orders']}</b> ta\n"
        f"⏳ Kutilayotgan to'lovlar: <b>{stats['pending_payments']}</b> ta\n\n"
        f"💳 <b>Hozirgi karta:</b> <code>{settings_service.get_card_number()}</code>\n"
        f"👤 <b>Izoh / Karta egasi:</b> <code>{settings_service.get_card_comment()}</code>\n\n"
        "<i>Quyidagi bo'limlardan birini tanlang:</i>"
    )

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_main_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_keyboard())
    await callback.answer()

@admin_router.callback_query(F.data == "adm_exit")
async def callback_admin_exit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("📩 Asosiy foydalanuvchi menyusidasiz.", reply_markup=get_main_menu_keyboard())
    await callback.answer("Admin paneldan chiqildi")

# --- CARD SETTINGS MENU ---

@admin_router.callback_query(F.data == "adm_card_menu")
async def callback_admin_card_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.clear()
    card_num = settings_service.get_card_number()
    card_comment = settings_service.get_card_comment()

    text = (
        "💳 <b>To'lov Karta Sozlamalari</b>\n\n"
        f"🔹 <b>Karta raqami:</b> <code>{card_num}</code>\n"
        f"🔹 <b>Izoh / Karta egasi:</b> <code>{card_comment}</code>\n\n"
        "Foydalanuvchilar 'Pul kiritish' bo'limiga kirganida ushbu karta ko'rsatiladi.\n"
        "O'zgartirish uchun quyidagi tugmalardan birini bosing:"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_card_keyboard())
    await callback.answer()

@admin_router.callback_query(F.data == "adm_edit_card_num")
async def callback_edit_card_num(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_card_number)
    text = (
        "✍️ <b>Yangi to'lov karta raqamini yuboring:</b>\n\n"
        f"Hozirgi karta: <code>{settings_service.get_card_number()}</code>\n"
        "Namuna: <code>8600 1234 5678 9012</code> yoki <code>9860123456789012</code>\n\n"
        "<i>Bekor qilish uchun '❌ Bekor qilish' tugmasini bosing.</i>"
    )
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    await callback.answer()

@admin_router.message(AdminStates.waiting_for_card_number)
async def process_new_card_number(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    new_card = message.text.strip()
    digits_only = "".join(filter(str.isdigit, new_card))
    if len(digits_only) < 12:
        await message.answer(
            "⚠️ Karta raqami noto'g'ri ko'rinadi (kamida 12-16 ta raqam bo'lishi kerak).\nQaytadan kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        return

    settings_service.set_card_number(new_card)
    await state.clear()

    await message.answer(
        f"✅ <b>Karta raqami muvaffaqiyatli o'zgartirildi!</b>\n\nYangi karta: <code>{new_card}</code>",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    # Re-show admin menu
    stats = await db.get_admin_stats()
    text = (
        "👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        f"💳 <b>Yangi karta:</b> <code>{new_card}</code>\n"
        f"👤 <b>Izoh / Karta egasi:</b> <code>{settings_service.get_card_comment()}</code>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_keyboard())

@admin_router.callback_query(F.data == "adm_edit_card_comment")
async def callback_edit_card_comment(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_card_comment)
    text = (
        "✍️ <b>Yangi izoh yoki karta egasining ismini yuboring:</b>\n\n"
        f"Hozirgi izoh: <code>{settings_service.get_card_comment()}</code>\n"
        "Namuna: <code>Xushnud B.</code> yoki <code>8048583227</code>\n\n"
        "<i>Bekor qilish uchun '❌ Bekor qilish' tugmasini bosing.</i>"
    )
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    await callback.answer()

@admin_router.message(AdminStates.waiting_for_card_comment)
async def process_new_card_comment(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    new_comment = message.text.strip()
    settings_service.set_card_comment(new_comment)
    await state.clear()

    await message.answer(
        f"✅ <b>Izoh / Karta egasi muvaffaqiyatli o'zgartirildi!</b>\n\nYangi izoh: <code>{new_comment}</code>",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    # Re-show admin menu
    text = (
        "👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        f"💳 <b>Hozirgi karta:</b> <code>{settings_service.get_card_number()}</code>\n"
        f"👤 <b>Izoh / Karta egasi:</b> <code>{new_comment}</code>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_keyboard())

# --- START MESSAGE SETTINGS MENU ---

@admin_router.callback_query(F.data == "adm_start_menu")
async def callback_admin_start_menu(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.clear()
    current_raw = settings_service.get_raw_welcome_message()
    text = (
        "✉️ <b>Start (Kirish) Xabari Sozlamalari</b>\n\n"
        "Foydalanuvchi <code>/start</code> bosganda unga ko'rinadigan xabarni bu yerdan boshqarishingiz mumkin.\n"
        "Matnda <code>{first_name}</code> yozsangiz, u foydalanuvchining ismi bilan avtomatik almashadi.\n\n"
        f"<b>Hozirgi matn:</b>\n<i>{current_raw}</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_start_msg_keyboard())
    await callback.answer()

@admin_router.callback_query(F.data == "adm_preview_start_text")
async def callback_preview_start_text(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    preview_text = settings_service.get_welcome_message(first_name=callback.from_user.first_name or "Foydalanuvchi")
    await callback.message.answer(
        f"👁 <b>Foydalanuvchiga ko'rinish namunasi (Preview):</b>\n\n{preview_text}",
        parse_mode="HTML"
    )
    await callback.answer()

@admin_router.callback_query(F.data == "adm_reset_start_text")
async def callback_reset_start_text(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    settings_service.reset_welcome_message()
    await callback.answer("✅ Start xabari standart holatga qaytarildi!", show_alert=True)
    
    current_raw = settings_service.get_raw_welcome_message()
    text = (
        "✉️ <b>Start (Kirish) Xabari Sozlamalari</b>\n\n"
        "✅ Start xabari standart holatga qaytarildi!\n\n"
        f"<b>Hozirgi matn:</b>\n<i>{current_raw}</i>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_start_msg_keyboard())

@admin_router.callback_query(F.data == "adm_edit_start_text")
async def callback_edit_start_text(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_start_message)
    text = (
        "✍️ <b>Yangi Start (Kirish) xabarini yozib yuboring:</b>\n\n"
        "Foydalanuvchi ismini chiqarish uchun <code>{first_name}</code> tegidan foydalanishingiz mumkin.\n"
        "HTML teglari (<b>qalin</b>, <i>kursiv</i>, <code>kod</code>) qo'llab-quvvatlanadi.\n\n"
        "<i>Bekor qilish uchun '❌ Bekor qilish' tugmasini bosing.</i>"
    )
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    await callback.answer()

@admin_router.message(AdminStates.waiting_for_start_message)
async def process_new_start_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    new_text = message.text.strip()
    settings_service.set_welcome_message(new_text)
    await state.clear()

    await message.answer(
        "✅ <b>Start xabari muvaffaqiyatli saqlandi!</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    
    preview = settings_service.get_welcome_message(first_name=message.from_user.first_name or "Foydalanuvchi")
    await message.answer(
        f"👁 <b>Yangi xabarning ko'rinishi:</b>\n\n{preview}",
        parse_mode="HTML",
        reply_markup=get_admin_main_keyboard()
    )

# --- /add_balance COMMAND & FSM ---

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

@admin_router.callback_query(F.data == "adm_add_bal")
async def callback_admin_add_bal_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_add_balance_user_id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("✍️ Balans qo'shmoqchi bo'lgan foydalanuvchining <b>Telegram ID</b>sini yuboring:", parse_mode="HTML", reply_markup=get_cancel_keyboard())
    await callback.answer()

@admin_router.message(AdminStates.waiting_for_add_balance_user_id)
async def process_admin_target_user(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamli Telegram ID kiriting:", reply_markup=get_cancel_keyboard())
        return

    await state.update_data(target_user_id=int(text))
    await state.set_state(AdminStates.waiting_for_add_balance_amount)
    await message.answer(f"💰 Foydalanuvchi (ID: <code>{text}</code>) uchun qo'shiladigan <b>summani (so'mda)</b> kiriting:", parse_mode="HTML", reply_markup=get_cancel_keyboard())

@admin_router.message(AdminStates.waiting_for_add_balance_amount)
async def process_admin_target_amount(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat musbat son kiriting:", reply_markup=get_cancel_keyboard())
        return

    amount = int(text)
    data = await state.get_data()
    target_id = data.get("target_user_id")

    success = await db.update_balance(target_id, amount, is_deposit=True)
    await state.clear()

    if success:
        amount_fmt = f"{amount:,}".replace(",", " ")
        await message.answer(f"✅ Foydalanuvchi <code>{target_id}</code> hisobiga <b>{amount_fmt} so'm</b> qo'shildi!", parse_mode="HTML", reply_markup=get_main_menu_keyboard())
        try:
            await bot.send_message(
                chat_id=target_id,
                text=f"💳 <b>Hisobingiz to'ldirildi!</b>\n\nBalansingizga <b>+{amount_fmt} so'm</b> qo'shildi.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Could not notify user {target_id}: {e}")
    else:
        await message.answer(f"❌ Foydalanuvchi {target_id} topilmadi.", reply_markup=get_main_menu_keyboard())

# --- STATS & CHANNELS & AUDIT LOGS ---

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
        f"💳 Kutilayotgan to'lov cheklari: <b>{stats['pending_payments']} ta</b>\n"
        f"✅ Bajarilgan buyurtmalar: <b>{stats.get('completed_orders', 0)} ta</b>"
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

@admin_router.callback_query(F.data == "adm_audit_logs")
async def callback_admin_audit_logs(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    logs = await admin_service.get_audit_logs(callback.from_user.id, limit=10)
    if not logs:
        text = "📋 <b>Audit Loglar:</b>\n\nHozircha audit yozuvlari mavjud emas."
    else:
        lines = ["📋 <b>Oxirgi Audit Loglar:</b>\n"]
        for log in logs:
            lines.append(f"• <code>[{log.created_at[:19] if log.created_at else ''}]</code> User: <code>{log.user_id}</code> | Action: <b>{log.action}</b>")
        text = "\n".join(lines)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_main_keyboard())
    await callback.answer()

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
    await callback.message.edit_text(f"✅ To'lov #{payment_id} tasdiqlandi. Foydalanuvchi (<code>{user_id}</code>) hisobiga <b>{amount_fmt} so'm</b> qo'shildi!", parse_mode="HTML")
    
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
    await message.answer(f"✅ To'lov #{payment_id} tasdiqlandi! Foydalanuvchi (<code>{user_id}</code>) ga <b>{amount_fmt} so'm</b> qo'shildi.", parse_mode="HTML", reply_markup=get_main_menu_keyboard())

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
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.reply(f"❌ To'lov #{payment_id} rad etildi.")

    try:
        await bot.send_message(
            chat_id=user_id,
            text="❌ <b>To'lov chekingiz rad etildi!</b>\n\nChekda ma'lumotlar to'liq emas yoki to'lov tasdiqlanmadi. Savollar bo'lsa adminga murojaat qiling.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Could not notify user {user_id}: {e}")
    await callback.answer()
