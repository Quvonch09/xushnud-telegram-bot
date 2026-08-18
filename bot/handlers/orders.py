import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.database import db, OrderModel
from bot.keyboards.reply import get_main_menu_keyboard, get_cancel_keyboard
from bot.keyboards.inline import (
    get_platforms_keyboard,
    get_categories_keyboard,
    get_services_keyboard,
    get_service_detail_keyboard,
    get_order_confirmation_keyboard,
    get_payment_systems_keyboard
)
from bot.services import smm_service
from bot.states import OrderStates

orders_router = Router(name="orders_router")

# --- LEVEL 1: PLATFORM SELECTION ---

@orders_router.message(F.text.in_(["🛒 Buyurtma berish", "Buyurtma berish"]))
async def handle_buyurtma_berish(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "➤ O'zingizga kerakli tarmoqni tanlang:",
        reply_markup=get_platforms_keyboard()
    )

@orders_router.callback_query(F.data == "back_to_platforms")
async def callback_back_to_platforms(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "➤ O'zingizga kerakli tarmoqni tanlang:",
        reply_markup=get_platforms_keyboard()
    )
    await callback.answer()

# --- LEVEL 2: CATEGORY SELECTION ---

@orders_router.callback_query(F.data.startswith("platform_"))
async def callback_platform_selected(callback: CallbackQuery):
    platform = callback.data.split("_")[1]
    if platform == "all":
        # Show all Telegram categories by default or all platforms
        platform = "Telegram"

    categories = await db.get_categories_by_platform(platform)
    if not categories:
        categories = ["Obunachi", "Ko'rishlar", "Reaksiya"]

    await callback.message.edit_text(
        "➡️ Kerakli xizmat turini tanlang:",
        reply_markup=get_categories_keyboard(platform, categories)
    )
    await callback.answer()

@orders_router.callback_query(F.data.startswith("back_to_cats_"))
async def callback_back_to_categories(callback: CallbackQuery):
    platform = callback.data.split("_")[3]
    categories = await db.get_categories_by_platform(platform)
    await callback.message.edit_text(
        "➡️ Kerakli xizmat turini tanlang:",
        reply_markup=get_categories_keyboard(platform, categories)
    )
    await callback.answer()

# --- LEVEL 3: SERVICES LIST ---

@orders_router.callback_query(F.data.startswith("cat_"))
async def callback_category_selected(callback: CallbackQuery):
    parts = callback.data.split("_")
    platform = parts[1]
    category = parts[2]

    services = await db.get_services(platform=platform, category=category)
    if not services:
        await callback.answer("Hozirda bu bo'limda xizmatlar mavjud emas.", show_alert=True)
        return

    await callback.message.edit_text(
        "➡️ O'zingizga kerakli xizmatni tanlang:",
        reply_markup=get_services_keyboard(platform, category, services)
    )
    await callback.answer()

@orders_router.callback_query(F.data.startswith("back_to_srv_list_"))
async def callback_back_to_service_list(callback: CallbackQuery):
    parts = callback.data.split("_")
    platform = parts[4]
    category = parts[5]

    services = await db.get_services(platform=platform, category=category)
    await callback.message.edit_text(
        "➡️ O'zingizga kerakli xizmatni tanlang:",
        reply_markup=get_services_keyboard(platform, category, services)
    )
    await callback.answer()

# --- LEVEL 4: SERVICE DETAIL ---

@orders_router.callback_query(F.data.startswith("srv_"))
async def callback_service_detail(callback: CallbackQuery):
    service_id = int(callback.data.split("_")[1])
    service = await db.get_service_by_id(service_id)
    if not service:
        await callback.answer("Xizmat topilmadi.", show_alert=True)
        return

    price_str = "0" if service.is_free else f"{service.price_per_1000:,}".replace(",", " ")
    desc = service.description or "Faqat ommaviy kanal va guruhlar uchun ishlaydi!"

    text = (
        f"🛒 <b>{service.name}</b>\n\n"
        f"⚙️ Xizmat IDsi: <code>{service.service_id_external or service.id}</code>\n"
        f"💎 Narxi (1000 ta) - <b>{price_str} so'm</b>\n"
        f"↕️ Minimal buyurtma: <b>{service.min_order} ta</b>\n"
        f"↕️ Maksimal buyurtma: <b>{service.max_order} ta</b>\n\n"
        f"⚠️ {desc}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_service_detail_keyboard(service)
    )
    await callback.answer()

# --- FSM ORDER CREATION FLOW ---

@orders_router.callback_query(F.data.startswith("order_now_"))
async def callback_order_now(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[2])
    service = await db.get_service_by_id(service_id)
    if not service:
        await callback.answer("Xizmat topilmadi.", show_alert=True)
        return

    await state.set_state(OrderStates.waiting_for_link)
    await state.update_data(service_id=service_id)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "Havolani yuboring (Kanal/guruh/post linki):",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@orders_router.message(OrderStates.waiting_for_link)
async def process_order_link(message: Message, state: FSMContext):
    link = message.text.strip()
    if link == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Buyurtma bekor qilindi.\n\n📩 Asosiy menyudasiz", reply_markup=get_main_menu_keyboard())
        return

    # Basic link validation
    if not (link.startswith("http://") or link.startswith("https://") or link.startswith("t.me/") or link.startswith("@")):
        await message.answer("⚠️ Noto'g'ri havola formati! Iltimos to'g'ri havola yuboring (masalan: https://t.me/kanal_nomi yoki @kanal_nomi):")
        return

    data = await state.get_data()
    service_id = data.get("service_id")
    service = await db.get_service_by_id(service_id)
    if not service:
        await state.clear()
        await message.answer("Xizmat ma'lumotlari topilmadi.", reply_markup=get_main_menu_keyboard())
        return

    await state.update_data(link=link)
    await state.set_state(OrderStates.waiting_for_quantity)

    min_qty = service.min_order
    max_qty = service.max_order

    await message.answer(
        f"Nechta kerak? (Min {min_qty} - Max {max_qty}):",
        reply_markup=get_cancel_keyboard()
    )

@orders_router.message(OrderStates.waiting_for_quantity)
async def process_order_quantity(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Buyurtma bekor qilindi.\n\n📩 Asosiy menyudasiz", reply_markup=get_main_menu_keyboard())
        return

    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat musbat butun son kiriting:")
        return

    quantity = int(text)
    data = await state.get_data()
    service_id = data.get("service_id")
    service = await db.get_service_by_id(service_id)
    if not service:
        await state.clear()
        await message.answer("Xizmat ma'lumotlari topilmadi.", reply_markup=get_main_menu_keyboard())
        return

    if quantity < service.min_order or quantity > service.max_order:
        await message.answer(
            f"⚠️ Miqdor chegaradan tashqarida! Minimal: {service.min_order}, Maksimal: {service.max_order} ta bo'lishi kerak.\nQaytadan kiriting:"
        )
        return

    # Calculate price
    if service.is_free:
        total_price = 0
    else:
        total_price = int((quantity / 1000.0) * service.price_per_1000)

    await state.update_data(quantity=quantity, total_price=total_price, service_name=service.name)
    await state.set_state(OrderStates.waiting_for_confirmation)

    price_formatted = f"{total_price:,}".replace(",", " ")
    summary_text = (
        "🧾 <b>Buyurtma ma'lumotlari:</b>\n\n"
        f"🛒 Xizmat: <b>{service.name}</b>\n"
        f"🔗 Havola: <code>{data.get('link')}</code>\n"
        f"🔢 Miqdor: <b>{quantity:,} ta</b>\n".replace(",", " ") +
        f"💰 Umumiy narxi: <b>{price_formatted} so'm</b>\n\n"
        "Buyurtmani tasdiqlaysizmi?"
    )

    await message.answer(
        summary_text,
        parse_mode="HTML",
        reply_markup=get_order_confirmation_keyboard()
    )

@orders_router.callback_query(F.data == "confirm_order", OrderStates.waiting_for_confirmation)
async def callback_confirm_order(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    service_id = data.get("service_id")
    link = data.get("link")
    quantity = data.get("quantity")
    total_price = data.get("total_price", 0)
    service_name = data.get("service_name", "")

    user = await db.get_user(user_id)
    if not user:
        user, _ = await db.create_or_get_user(user_id, callback.from_user.username, callback.from_user.first_name)

    service = await db.get_service_by_id(service_id)
    is_free = service.is_free if service else False

    # Balance check (free service bypasses balance requirement)
    if not is_free and user.balance < total_price:
        bal_fmt = f"{user.balance:,}".replace(",", " ")
        prc_fmt = f"{total_price:,}".replace(",", " ")
        await state.clear()
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            f"❌ <b>Hisobingizda mablag' yetarli emas!</b>\n\n"
            f"Buyurtma narxi: <b>{prc_fmt} so'm</b>\n"
            f"Sizning balansingiz: <b>{bal_fmt} so'm</b>\n\n"
            "Iltimos, avval hisobingizni to'ldiring:",
            parse_mode="HTML",
            reply_markup=get_payment_systems_keyboard()
        )
        await callback.answer()
        return

    # Deduct balance if not free
    if not is_free and total_price > 0:
        await db.update_balance(user_id, -total_price)

    # Call SMM API
    ext_id = service.service_id_external if service else service_id
    smm_resp = await smm_service.create_order(
        service_id=ext_id or 1,
        link=link,
        quantity=quantity,
        is_free=is_free
    )

    order_status = "Completed" if is_free else "InProgress"
    external_order_id = smm_resp.get("order_id", "N/A")

    # Create order in DB
    new_order = OrderModel(
        user_telegram_id=user_id,
        service_id=service_id,
        service_name=service_name,
        link=link,
        quantity=quantity,
        price=total_price,
        status=order_status,
        external_order_id=external_order_id
    )
    saved_order = await db.create_order(new_order)
    order_db_id = saved_order.id if saved_order else "NEW"

    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass

    price_formatted = f"{total_price:,}".replace(",", " ")
    status_emoji = "✅ Bajarildi" if is_free else "⏳ Jarayonda"

    success_msg = (
        "✅ <b>Buyurtmangiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"🆔 Buyurtma ID: <b>#{order_db_id}</b>\n"
        f"🛒 Xizmat: <b>{service_name}</b>\n"
        f"🔢 Miqdor: <b>{quantity:,} ta</b>\n".replace(",", " ") +
        f"💰 Narxi: <b>{price_formatted} so'm</b>\n"
        f"Holat: <b>{status_emoji}</b>"
    )

    await callback.message.answer(
        success_msg,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@orders_router.callback_query(F.data == "cancel_order")
async def callback_cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("❌ Buyurtma bekor qilindi.\n\n📩 Asosiy menyudasiz", reply_markup=get_main_menu_keyboard())
    await callback.answer()

# --- BUYURTMALAR HISTORY ---

@orders_router.message(F.text.in_(["👣 Buyurtmalar", "🐾 Buyurtmalar", "Buyurtmalar"]))
async def handle_orders_history(message: Message):
    user_id = message.from_user.id
    orders = await db.get_user_orders(user_id, limit=10)

    if not orders:
        await message.answer("Sizda buyurtma topilmadi.")
        return

    status_emojis = {
        "Pending": "⏳ Kutilmoqda",
        "InProgress": "🚀 Jarayonda",
        "Completed": "✅ Bajarildi",
        "Canceled": "❌ Bekor qilindi"
    }

    lines = ["🐾 <b>Sizning oxirgi buyurtmalaringiz:</b>\n"]
    for o in orders:
        st = status_emojis.get(o.status, o.status)
        price_fmt = f"{o.price:,}".replace(",", " ")
        lines.append(
            f"🆔 <b>Buyurtma #{o.id}</b>\n"
            f"🛒 Xizmat: {o.service_name or 'SMM xizmat'}\n"
            f"🔢 Miqdor: {o.quantity} ta\n"
            f"💰 Narxi: {price_fmt} so'm\n"
            f"Holat: {st}\n"
            f"────────────────"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")
