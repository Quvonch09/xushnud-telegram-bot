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
    get_reaction_emojis_keyboard,
    get_poll_options_keyboard,
    get_order_confirmation_keyboard,
    get_payment_systems_keyboard
)
from bot.services import order_service, mock_provider
from bot.states import OrderStates

orders_router = Router(name="orders_router")

# --- LEVEL 1: PLATFORM SELECTION ---

@orders_router.message(F.text.in_(["🛒 Buyurtma berish", "Buyurtma berish"]))
async def handle_buyurtma_berish(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "➤ <b>Ijtimoiy tarmoqni tanlang:</b>\n"
        "<i>Kerakli tarmoqni tanlab, xizmat turini ko'ring:</i>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_platforms_keyboard())

@orders_router.callback_query(F.data == "back_to_platforms")
async def callback_back_to_platforms(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = "➤ <b>Ijtimoiy tarmoqni tanlang:</b>"
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

    text = f"▶️ <b>Xizmat turini tanlang ({platform}):</b>"
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
    text = f"▶️ <b>Xizmat turini tanlang ({platform}):</b>"
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
        await callback.answer("Bu bo'limda hozircha xizmatlar mavjud emas.", show_alert=True)
        return

    text = (
        f"📋 <b>{platform} — {category}</b> (Xizmatlar ro'yxati):\n"
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
    text = f"📋 <b>{platform} — {category}</b> (Xizmatlar ro'yxati):"
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

    price_str = "Tekin" if service.is_free or service.price_per_1000 == 0 else f"{service.price_per_1000:,} so'm".replace(",", " ")
    text = (
        f"📦 <b>Xizmat:</b> {service.name}\n"
        f"🏷 <b>Platforma:</b> {service.platform} ({service.category})\n"
        f"💰 <b>Narx (1 000 ta uchun):</b> {price_str}\n"
        f"📉 <b>Minimal miqdor:</b> {service.min_order:,} ta\n"
        f"📈 <b>Maksimal miqdor:</b> {service.max_order:,} ta\n"
        f"⏱ <b>Bajarilish vaqti:</b> {service.estimated_time or '1-5 daqiqa'}\n\n"
        f"ℹ️ <i>{service.description}</i>"
    ).replace(",", " ")

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_service_detail_keyboard(service)
    )
    await callback.answer()

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
        requires_reaction=service.requires_reaction,
        requires_poll_option=service.requires_poll_option,
        estimated_time=service.estimated_time or "1-5 daqiqa"
    )

    link_prompt = (
        f"🔗 <b>Buyurtma uchun havola yuboring:</b>\n\n"
        f"Paket: <b>{service.name}</b>\n"
        f"Namuna: <code>https://t.me/kanal_nomi</code> yoki <code>@kanal_nomi</code>"
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(link_prompt, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    await callback.answer()

# --- LEVEL 5: FSM INPUT - LINK ---

@orders_router.message(OrderStates.waiting_for_link)
async def process_order_link(message: Message, state: FSMContext):
    link = message.text.strip()
    data = await state.get_data()
    platform = data.get("platform", "Telegram")
    service_id = data.get("service_id", 1)

    # Validate link format
    is_valid, err_msg = mock_provider.validate_url(link, platform)
    if not is_valid:
        await message.answer(
            f"❌ <b>Xatolik:</b> {err_msg}\n\nIltimos, to'g'ri havola yuboring:",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(order_link=link)

    # If service requires reaction emoji selection
    if data.get("requires_reaction"):
        await state.set_state(OrderStates.waiting_for_reaction_emoji)
        text = (
            "❤️ <b>Qo'shilishi kerak bo'lgan reaksiya emojisini tanlang:</b>\n"
            "Quyidagi tugmalardan birini bosing yoki o'zingiz istagan emojini yuboring:"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=get_reaction_emojis_keyboard(service_id))
        return

    # If service requires poll option selection
    if data.get("requires_poll_option"):
        await state.set_state(OrderStates.waiting_for_poll_option)
        text = (
            "🗳 <b>So'rovnoma variant raqamini tanlang:</b>\n"
            "Qaysi variantga ovoz berilishini ko'rsating (Masalan: 1, 2, 3...):"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=get_poll_options_keyboard(service_id))
        return

    # Regular flow: proceed to quantity
    await state.set_state(OrderStates.waiting_for_quantity)
    min_ord = data.get("min_order", 10)
    max_ord = data.get("max_order", 100000)

    text = (
        f"🔢 <b>Buyurtma miqdorini kiriting:</b>\n\n"
        f"Minimal miqdor: <b>{min_ord:,}</b> ta\n"
        f"Maksimal miqdor: <b>{max_ord:,}</b> ta\n\n"
        f"<i>Faqat butun son yuboring (Masalan: 100).</i>"
    ).replace(",", " ")

    await message.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())

# --- LEVEL 5.1: REACTION SELECTION HANDLERS ---

@orders_router.callback_query(F.data.startswith("set_react_"))
async def callback_set_reaction_emoji(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    emoji_val = parts[3]
    await state.update_data(reaction_type=emoji_val)
    await state.set_state(OrderStates.waiting_for_quantity)

    data = await state.get_data()
    min_ord = data.get("min_order", 10)
    max_ord = data.get("max_order", 100000)

    text = (
        f"Tanlangan reaksiya: <b>{emoji_val}</b>\n\n"
        f"🔢 <b>Endi buyurtma miqdorini kiriting:</b>\n"
        f"Minimal: <b>{min_ord:,}</b> ta | Maksimal: <b>{max_ord:,}</b> ta"
    ).replace(",", " ")

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    await callback.answer()

@orders_router.message(OrderStates.waiting_for_reaction_emoji)
async def process_custom_reaction_emoji(message: Message, state: FSMContext):
    emoji_val = message.text.strip()
    await state.update_data(reaction_type=emoji_val)
    await state.set_state(OrderStates.waiting_for_quantity)

    data = await state.get_data()
    min_ord = data.get("min_order", 10)
    max_ord = data.get("max_order", 100000)

    text = (
        f"Tanlangan reaksiya: <b>{emoji_val}</b>\n\n"
        f"🔢 <b>Endi buyurtma miqdorini kiriting:</b>\n"
        f"Minimal: <b>{min_ord:,}</b> ta | Maksimal: <b>{max_ord:,}</b> ta"
    ).replace(",", " ")

    await message.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())

# --- LEVEL 5.2: POLL OPTION SELECTION HANDLERS ---

@orders_router.callback_query(F.data.startswith("set_poll_"))
async def callback_set_poll_option(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    opt_val = parts[3]
    await state.update_data(poll_option=opt_val)
    await state.set_state(OrderStates.waiting_for_quantity)

    data = await state.get_data()
    min_ord = data.get("min_order", 10)
    max_ord = data.get("max_order", 100000)

    text = (
        f"Tanlangan variant: <b>{opt_val}-variant</b>\n\n"
        f"🔢 <b>Endi ovozlar miqdorini kiriting:</b>\n"
        f"Minimal: <b>{min_ord:,}</b> ta | Maksimal: <b>{max_ord:,}</b> ta"
    ).replace(",", " ")

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    await callback.answer()

@orders_router.message(OrderStates.waiting_for_poll_option)
async def process_custom_poll_option(message: Message, state: FSMContext):
    opt_val = message.text.strip()
    await state.update_data(poll_option=opt_val)
    await state.set_state(OrderStates.waiting_for_quantity)

    data = await state.get_data()
    min_ord = data.get("min_order", 10)
    max_ord = data.get("max_order", 100000)

    text = (
        f"Tanlangan variant: <b>{opt_val}</b>\n\n"
        f"🔢 <b>Endi ovozlar miqdorini kiriting:</b>\n"
        f"Minimal: <b>{min_ord:,}</b> ta | Maksimal: <b>{max_ord:,}</b> ta"
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

    # Calculate price
    price_per_1000 = data.get("price_per_1000", 0)
    is_free = data.get("is_free", False)
    total_price = 0 if is_free else int((quantity * price_per_1000) / 1000)

    await state.update_data(quantity=quantity, total_price=total_price)
    await state.set_state(OrderStates.waiting_for_confirmation)

    price_fmt = "Tekin" if total_price == 0 else f"{total_price:,} so'm".replace(",", " ")
    estimated_time = data.get("estimated_time", "1-5 daqiqa")

    extra_lines = []
    if data.get("reaction_type"):
        extra_lines.append(f"❤️ <b>Reaksiya:</b> {data.get('reaction_type')}")
    if data.get("poll_option"):
        extra_lines.append(f"🗳 <b>Variant:</b> {data.get('poll_option')}")
    extra_info_str = ("\n" + "\n".join(extra_lines)) if extra_lines else ""

    confirm_text = (
        "📋 <b>BUYURTMANI TASDIQLASH:</b>\n\n"
        f"🔹 <b>Xizmat nomi:</b> {data.get('service_name')}\n"
        f"🔗 <b>Havola:</b> <code>{data.get('order_link')}</code>"
        f"{extra_info_str}\n"
        f"🔢 <b>Miqdor:</b> {quantity:,} ta\n"
        f"💰 <b>Narx:</b> <b>{price_fmt}</b>\n"
        f"⏱ <b>Bajarilish vaqti:</b> {estimated_time}\n\n"
        "<i>Buyurtmani tasdiqlash uchun quyidagi tugmani bosing:</i>"
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
    reaction_type = data.get("reaction_type")
    poll_option = data.get("poll_option")

    # Call OrderService
    res = await order_service.validate_and_create_order(
        user_telegram_id=user_id,
        service_id=service_id,
        link=link,
        quantity=quantity,
        reaction_type=reaction_type,
        poll_option=poll_option
    )

    await state.clear()

    if not res["success"]:
        if res.get("need_deposit"):
            text = (
                f"❌ <b>{res['error']}</b>\n\n"
                "Quyidagi tugma orqali hisobingizni to'ldirishingiz mumkin:"
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_payment_systems_keyboard())
        else:
            await callback.message.edit_text(f"❌ <b>Xatolik:</b> {res['error']}", parse_mode="HTML")
        await callback.answer()
        return

    order = res["order"]
    price_fmt = f"{order.price:,} so'm".replace(",", " ")

    extra_details = []
    if reaction_type:
        extra_details.append(f"❤️ <b>Reaksiya:</b> {reaction_type}")
    if poll_option:
        extra_details.append(f"🗳 <b>Variant:</b> {poll_option}")
    extra_details_str = ("\n" + "\n".join(extra_details)) if extra_details else ""

    success_text = (
        f"✅ <b>Buyurtma muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"🆔 <b>Buyurtma ID:</b> <code>#{order.id}</code>\n"
        f"📦 <b>Xizmat:</b> {order.service_name}\n"
        f"🔗 <b>Havola:</b> {order.link}"
        f"{extra_details_str}\n"
        f"🔢 <b>Miqdor:</b> {order.quantity:,} ta\n"
        f"💰 <b>Yechilgan summa:</b> {price_fmt}\n"
        f"🚀 <b>Holat:</b> Jarayonda\n"
        f"⏱ <b>Bajarilish vaqti:</b> {res['estimated_time']}\n\n"
        "<i>Buyurtmangiz navbatga qo'yildi va tez orada bajariladi.</i>"
    ).replace(",", " ")

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(success_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    await callback.answer("✅ Buyurtma qabul qilindi!")

@orders_router.callback_query(OrderStates.waiting_for_confirmation, F.data == "cancel_order")
async def callback_cancel_confirmation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("❌ Buyurtma bekor qilindi.\n\n📩 Asosiy menyudasiz", reply_markup=get_main_menu_keyboard())
    await callback.answer()

# --- BUYURTMALAR HISTORY ---

@orders_router.message(F.text.in_(["🐾 Buyurtmalar", "👣 Buyurtmalar", "Buyurtmalar"]))
async def handle_orders_history(message: Message):
    user_id = message.from_user.id
    orders = await order_service.get_user_orders(user_id, limit=10)

    if not orders:
        await message.answer(
            "Sizda hali buyurtmalar mavjud emas.",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return

    status_labels = {
        "demo_pending": "⏳ Kutilmoqda",
        "demo_paid": "💳 To'landi",
        "demo_processing": "🚀 Jarayonda",
        "demo_completed": "✅ Bajarildi",
        "demo_cancelled": "❌ Bekor qilindi",
        "Pending": "⏳ Kutilmoqda",
        "InProgress": "🚀 Jarayonda",
        "Completed": "✅ Bajarildi",
        "Canceled": "❌ Bekor qilindi"
    }

    lines = ["🐾 <b>Sizning buyurtmalaringiz tarixi:</b>\n"]
    for o in orders:
        st_text = status_labels.get(o.status, o.status)
        price_fmt = f"{o.price:,} so'm".replace(",", " ")
        extra_info = ""
        if getattr(o, "reaction_type", None):
            extra_info += f" | Reaksiya: {o.reaction_type}"
        if getattr(o, "poll_option", None):
            extra_info += f" | Variant: {o.poll_option}"

        lines.append(
            f"🆔 <b>#{o.id}</b> | {o.service_name or 'Xizmat'}\n"
            f"🔗 <code>{o.link}</code>{extra_info}\n"
            f"🔢 Miqdor: {o.quantity:,} ta | Narx: {price_fmt}\n"
            f"Holat: <b>{st_text}</b>\n"
        )

    await message.answer("\n".join(lines).replace(",", " "), parse_mode="HTML", reply_markup=get_main_menu_keyboard())
