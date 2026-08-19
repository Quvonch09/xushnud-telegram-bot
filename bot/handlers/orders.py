import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.database import db
from bot.database.models import ServiceModel
from bot.keyboards.reply import get_main_menu_keyboard, get_cancel_keyboard
from bot.keyboards.inline import (
    get_platforms_keyboard,
    get_categories_keyboard,
    get_services_keyboard,
    get_service_detail_keyboard,
    get_order_confirmation_keyboard,
    get_payment_systems_keyboard
)
from bot.services import order_service, mock_provider
from bot.states import OrderStates

orders_router = Router(name="orders_router")

DEMO_BANNER = "🛡️ <b>[DEMO MODE — Faqat test simulyatsiyasi]</b>\n<i>Tashqi platformalarga hech qanday real so'rov yuborilmaydi.</i>\n\n"

# --- LEVEL 1: PLATFORM SELECTION ---

@orders_router.message(F.text.in_(["🛒 Buyurtma berish", "Buyurtma berish"]))
async def handle_buyurtma_berish(message: Message, state: FSMContext):
    await state.clear()
    text = (
        f"{DEMO_BANNER}"
        "➤ <b>Demo xizmat uchun ijtimoiy tarmoqni tanlang:</b>\n"
        "<i>Barcha xizmatlar xavfsiz lokal sandbox rejimida simulyatsiya qilinadi.</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_platforms_keyboard())

@orders_router.callback_query(F.data == "back_to_platforms")
async def callback_back_to_platforms(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        f"{DEMO_BANNER}"
        "➤ <b>Demo xizmat uchun ijtimoiy tarmoqni tanlang:</b>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_platforms_keyboard())
    await callback.answer()

# --- LEVEL 2: CATEGORY SELECTION ---

@orders_router.callback_query(F.data.startswith("platform_"))
async def callback_platform_selected(callback: CallbackQuery):
    platform = callback.data.split("_")[1]
    if platform == "all":
        platform = "Telegram"

    categories = await db.get_categories_by_platform(platform)
    if not categories:
        categories = ["Obunachi", "Ko'rishlar", "Reaksiya"]

    text = (
        f"{DEMO_BANNER}"
        f"▶️ <b>Demo xizmat turini tanlang ({platform}):</b>\n"
        "<i>Har bir xizmat faqat test simulyatsiyasi uchun ishlatiladi.</i>"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_categories_keyboard(platform, categories)
    )
    await callback.answer()

@orders_router.callback_query(F.data.startswith("back_to_cats_"))
async def callback_back_to_categories(callback: CallbackQuery):
    platform = callback.data.split("_")[3]
    categories = await db.get_categories_by_platform(platform)
    text = (
        f"{DEMO_BANNER}"
        f"▶️ <b>Demo xizmat turini tanlang ({platform}):</b>"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_categories_keyboard(platform, categories)
    )
    await callback.answer()

# --- LEVEL 3: SERVICE SELECTION ---

@orders_router.callback_query(F.data.startswith("cat_"))
async def callback_category_selected(callback: CallbackQuery):
    parts = callback.data.split("_")
    platform = parts[1]
    category = parts[2]

    services = await db.get_services_by_category(platform, category)
    if not services:
        await callback.answer("Bu bo'limda demo xizmatlar mavjud emas.", show_alert=True)
        return

    text = (
        f"{DEMO_BANNER}"
        f"📋 <b>{platform} — {category}</b> (Demo xizmatlar ro'yxati):\n"
        "Kerakli paketni tanlang:"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_services_keyboard(platform, category, services)
    )
    await callback.answer()

@orders_router.callback_query(F.data.startswith("back_to_srv_list_"))
async def callback_back_to_service_list(callback: CallbackQuery):
    parts = callback.data.split("_")
    platform = parts[4]
    category = parts[5]

    services = await db.get_services_by_category(platform, category)
    text = (
        f"{DEMO_BANNER}"
        f"📋 <b>{platform} — {category}</b> (Demo xizmatlar ro'yxati):"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_services_keyboard(platform, category, services)
    )
    await callback.answer()

# --- LEVEL 4: SERVICE DETAIL & INITIATE ORDER ---

@orders_router.callback_query(F.data.startswith("srv_"))
async def callback_service_detail(callback: CallbackQuery):
    service_id = int(callback.data.split("_")[1])
    service = await db.get_service_by_id(service_id)
    if not service:
        await callback.answer("Xizmat topilmadi!", show_alert=True)
        return

    price_str = "0 so'm (Tekin)" if service.is_free else f"{service.price_per_1000:,} so'm".replace(",", " ")
    text = (
        f"{DEMO_BANNER}"
        f"📦 <b>Demo xizmat:</b> {service.name}\n"
        f"🏷 <b>Platforma:</b> {service.platform} ({service.category})\n"
        f"💰 <b>Narx (1 000 ta uchun):</b> {price_str}\n"
        f"📉 <b>Minimal miqdor:</b> {service.min_order:,} ta\n"
        f"📈 <b>Maksimal miqdor:</b> {service.max_order:,} ta\n"
        f"⏱ <b>Bajarilish vaqti:</b> {service.estimated_time or '1-5 daqiqa (Demo)'}\n\n"
        f"ℹ️ <i>{service.description}</i>"
    ).replace(",", " ")

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_service_detail_keyboard(service)
    )
    await callback.answer()

# --- LEVEL 5: FSM INPUT - LINK ---

@orders_router.callback_query(F.data.startswith("order_now_"))
async def callback_order_now(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[2])
    service = await db.get_service_by_id(service_id)
    if not service:
        await callback.answer("Xizmat topilmadi!", show_alert=True)
        return

    await state.set_state(OrderStates.waiting_for_link)
    await state.update_data(
        service_id=service.id,
        service_name=service.name,
        platform=service.platform,
        price_per_1000=service.price_per_1000,
        min_order=service.min_order,
        max_order=service.max_order,
        is_free=service.is_free,
        estimated_time=service.estimated_time or "1-5 daqiqa (Demo)"
    )

    text = (
        f"{DEMO_BANNER}"
        f"🔗 <b>Demo buyurtma uchun havola yuboring:</b>\n\n"
        f"Paket: <b>{service.name}</b>\n"
        f"Namuna: <code>https://t.me/kanal_nomi</code> yoki <code>@kanal_nomi</code>\n\n"
        "<i>Eslatma: Server havolaga ulanmaydi, faqat sintaktik format tekshiriladi.</i>"
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    await callback.answer()

@orders_router.message(OrderStates.waiting_for_link)
async def process_order_link(message: Message, state: FSMContext):
    link = message.text.strip()
    data = await state.get_data()
    platform = data.get("platform", "Telegram")

    # Offline URL validation
    is_valid, err_msg = mock_provider.validate_url(link, platform)
    if not is_valid:
        await message.answer(
            f"❌ <b>Xatolik:</b> {err_msg}\n\nIltimos, to'g'ri demo havola yuboring:",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(order_link=link)
    await state.set_state(OrderStates.waiting_for_quantity)

    min_ord = data.get("min_order", 10)
    max_ord = data.get("max_order", 100000)

    text = (
        f"{DEMO_BANNER}"
        f"🔢 <b>Demo buyurtma miqdorini kiriting:</b>\n\n"
        f"Minimal miqdor: <b>{min_ord:,}</b> ta\n"
        f"Maksimal miqdor: <b>{max_ord:,}</b> ta\n\n"
        f"<i>Faqat butun son yuboring (Masalan: 100).</i>"
    ).replace(",", " ")

    await message.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())

# --- LEVEL 6: FSM INPUT - QUANTITY & CONFIRMATION ---

@orders_router.message(OrderStates.waiting_for_quantity)
async def process_order_quantity(message: Message, state: FSMContext):
    qty_text = message.text.strip()
    if not qty_text.isdigit():
        await message.answer(
            "❌ Iltimos, faqat musbat butun son kiriting (Masalan: 500):",
            reply_markup=get_cancel_keyboard()
        )
        return

    quantity = int(qty_text)
    data = await state.get_data()
    min_ord = data.get("min_order", 10)
    max_ord = data.get("max_order", 100000)

    if quantity < min_ord:
        await message.answer(
            f"❌ Minimal miqdor: {min_ord:,} ta. Qaytadan kiriting:".replace(",", " "),
            reply_markup=get_cancel_keyboard()
        )
        return

    if quantity > max_ord:
        await message.answer(
            f"❌ Maksimal miqdor: {max_ord:,} ta. Qaytadan kiriting:".replace(",", " "),
            reply_markup=get_cancel_keyboard()
        )
        return

    # Calculate price on server
    price_per_1000 = data.get("price_per_1000", 0)
    is_free = data.get("is_free", False)
    total_price = 0 if is_free else int((quantity * price_per_1000) / 1000)

    await state.update_data(quantity=quantity, total_price=total_price)
    await state.set_state(OrderStates.waiting_for_confirmation)

    price_fmt = "0 so'm (Tekin)" if total_price == 0 else f"{total_price:,} so'm".replace(",", " ")
    estimated_time = data.get("estimated_time", "1-5 daqiqa (Demo)")

    confirm_text = (
        f"{DEMO_BANNER}"
        "📋 <b>BUYURTMANI TASDIQLASH (DEMO):</b>\n\n"
        f"🔹 <b>Xizmat nomi:</b> {data.get('service_name')}\n"
        f"🔗 <b>Demo havola:</b> <code>{data.get('order_link')}</code>\n"
        f"🔢 <b>Demo miqdor:</b> {quantity:,} ta\n"
        f"💰 <b>Demo narx:</b> <b>{price_fmt}</b>\n"
        f"⏱ <b>Taxminiy demo bajarilish vaqti:</b> {estimated_time}\n\n"
        "<i>✅ 'Demo buyurtmani yaratish' tugmasini bosing:</i>"
    ).replace(",", " ")

    await message.answer(
        confirm_text,
        parse_mode="HTML",
        reply_markup=get_order_confirmation_keyboard()
    )

# --- LEVEL 7: CONFIRM ORDER ---

@orders_router.callback_query(OrderStates.waiting_for_confirmation, F.data == "confirm_order")
async def callback_confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    service_id = data.get("service_id")
    link = data.get("order_link")
    quantity = data.get("quantity")

    # Call OrderService (which enforces validation, server price, demo payment, and logging)
    res = await order_service.validate_and_create_order(
        user_telegram_id=user_id,
        service_id=service_id,
        link=link,
        quantity=quantity
    )

    await state.clear()

    if not res["success"]:
        if res.get("need_deposit"):
            text = (
                f"{DEMO_BANNER}"
                f"❌ <b>{res['error']}</b>\n\n"
                "Quyidagi tugma orqali hisobingizga demo mablag' kiritishingiz mumkin:"
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_payment_systems_keyboard())
        else:
            await callback.message.edit_text(f"❌ <b>Xatolik:</b> {res['error']}", parse_mode="HTML")
        await callback.answer()
        return

    order = res["order"]
    price_fmt = f"{order.price:,} so'm".replace(",", " ")

    success_text = (
        f"{DEMO_BANNER}"
        f"✅ <b>Demo buyurtma yaratildi!</b>\n\n"
        f"🆔 <b>Buyurtma ID:</b> <code>#{order.id}</code> (Demo: {order.external_order_id})\n"
        f"📦 <b>Xizmat:</b> {order.service_name}\n"
        f"🔗 <b>Havola:</b> {order.link}\n"
        f"🔢 <b>Miqdor:</b> {order.quantity:,} ta\n"
        f"💰 <b>Demo yechilgan summa:</b> {price_fmt}\n"
        f"🚀 <b>Status:</b> 🚀 Jarayonda (Demo simulyatsiya)\n"
        f"⏱ <b>Bajarilish vaqti:</b> {res['estimated_time']}\n\n"
        "<i>ℹ️ Bu buyurtma hech qanday tashqi platformaga yuborilmaydi.</i>"
    ).replace(",", " ")

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(success_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    await callback.answer("✅ Demo buyurtma qabul qilindi!")

@orders_router.callback_query(OrderStates.waiting_for_confirmation, F.data == "cancel_order")
async def callback_cancel_confirmation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("❌ Demo buyurtma bekor qilindi.\n\n📩 Asosiy menyudasiz", reply_markup=get_main_menu_keyboard())
    await callback.answer()

# --- BUYURTMALAR HISTORY ---

@orders_router.message(F.text.in_(["🐾 Buyurtmalar", "👣 Buyurtmalar", "Buyurtmalar"]))
async def handle_orders_history(message: Message):
    user_id = message.from_user.id
    orders = await order_service.get_user_orders(user_id, limit=10)

    if not orders:
        await message.answer(
            f"{DEMO_BANNER}Sizda hali demo buyurtmalar mavjud emas.",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return

    status_labels = {
        "demo_pending": "⏳ Kutilmoqda (Demo)",
        "demo_paid": "💳 To'landi (Demo)",
        "demo_processing": "🚀 Jarayonda (Demo)",
        "demo_completed": "✅ Bajarildi (Demo)",
        "demo_cancelled": "❌ Bekor qilindi (Demo)",
        "Pending": "⏳ Kutilmoqda (Demo)",
        "InProgress": "🚀 Jarayonda (Demo)",
        "Completed": "✅ Bajarildi (Demo)",
        "Canceled": "❌ Bekor qilindi (Demo)"
    }

    lines = [f"{DEMO_BANNER}🐾 <b>Sizning demo buyurtmalaringiz tarixi:</b>\n"]
    for o in orders:
        st_text = status_labels.get(o.status, o.status)
        price_fmt = f"{o.price:,} so'm".replace(",", " ")
        lines.append(
            f"🆔 <b>#{o.id}</b> | {o.service_name or 'Demo Xizmat'}\n"
            f"🔗 <code>{o.link}</code>\n"
            f"🔢 Miqdor: {o.quantity:,} ta | Narx: {price_fmt}\n"
            f"Holat: <b>{st_text}</b>\n"
        )

    await message.answer("\n".join(lines).replace(",", " "), parse_mode="HTML", reply_markup=get_main_menu_keyboard())
