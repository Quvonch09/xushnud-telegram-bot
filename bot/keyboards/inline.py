from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.database.models import ChannelModel, ServiceModel
from bot.config import settings

def get_webapp_keyboard(url: Optional[str] = None) -> InlineKeyboardMarkup:
    """
    Returns inline keyboard with 🚀 Ilovani ochish (Mini App) button.
    """
    target_url = url or settings.effective_webapp_url
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Ilovani ochish",
                web_app=WebAppInfo(url=target_url),
                style="primary"
            )
        ]
    ])


def get_subscription_keyboard(channels: List[ChannelModel]) -> InlineKeyboardMarkup:
    """
    Mandatory channel subscription keyboard with URL buttons and verification button.
    """
    keyboard = []
    for ch in channels:
        keyboard.append([
            InlineKeyboardButton(text=ch.name, url=ch.link, style="primary")
        ])
    keyboard.append([
        InlineKeyboardButton(text="☑️ Tekshirish", callback_data="check_subs", style="primary")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_raqam_olish_keyboard() -> InlineKeyboardMarkup:
    admin_link = f"https://t.me/{settings.SUPPORT_ADMIN.lstrip('@')}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Admin orqali olish", url=admin_link, style="primary")]
    ])

def get_platforms_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✈️ Telegram", callback_data="platform_Telegram", style="primary"),
            InlineKeyboardButton(text="📸 Instagram", callback_data="platform_Instagram", style="primary"),
        ],
        [
            InlineKeyboardButton(text="▶️ YouTube", callback_data="platform_YouTube", style="primary"),
            InlineKeyboardButton(text="🎵 TikTok", callback_data="platform_TikTok", style="primary"),
        ],
        [
            InlineKeyboardButton(text="📝 Barcha xizmatlar ↗️", callback_data="platform_all", style="primary"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main", style="primary"),
        ]
    ])

def get_categories_keyboard(platform: str, categories: List[str]) -> InlineKeyboardMarkup:
    """
    Xizmat turlari tanlash tugmalari
    """
    category_icons = {
        "Reaksiya": "🔥",
        "Ko'rishlar": "👁",
        "Obunachi": "👤",
        "Boost ovoz": "🔊",
        "Boostlar": "🚀",
        "Ovozlar": "🗳",
        "Hikoya": "🖼",
        "O'zbek tarmoq": "🇺🇿",
    }
    
    keyboard = []
    row = []
    for cat in categories:
        icon = category_icons.get(cat, "⚡")
        btn = InlineKeyboardButton(text=f"{icon} {cat}", callback_data=f"cat_{platform}_{cat}", style="primary")
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_platforms", style="primary")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_services_keyboard(platform: str, category: str, services: List[ServiceModel]) -> InlineKeyboardMarkup:
    keyboard = []
    for s in services:
        price_txt = "Tekin" if s.is_free or s.price_per_1000 == 0 else f"{s.price_per_1000:,} so'm".replace(",", " ")
        btn_text = f"{s.name} — {price_txt}"
        keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"srv_{s.id}", style="primary")
        ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"back_to_cats_{platform}", style="primary")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_service_detail_keyboard(service: ServiceModel) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="☑️ Buyurtma berish", callback_data=f"order_now_{service.id}", style="primary")
        ],
        [
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"back_to_srv_list_{service.platform}_{service.category}", style="primary")
        ]
    ])

def get_reaction_emojis_keyboard(service_id: int) -> InlineKeyboardMarkup:
    emojis = ["👍", "❤️", "🔥", "🎉", "🤩", "👏", "⚡", "🤝"]
    keyboard = []
    row = []
    for em in emojis:
        row.append(InlineKeyboardButton(text=em, callback_data=f"set_react_{service_id}_{em}", style="primary"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text="🎲 Aralash reaksiyalar", callback_data=f"set_react_{service_id}_mixed", style="primary")
    ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="cancel_order", style="primary")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_poll_options_keyboard(service_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="1-variant", callback_data=f"set_poll_{service_id}_1", style="primary"),
            InlineKeyboardButton(text="2-variant", callback_data=f"set_poll_{service_id}_2", style="primary")
        ],
        [
            InlineKeyboardButton(text="3-variant", callback_data=f"set_poll_{service_id}_3", style="primary"),
            InlineKeyboardButton(text="4-variant", callback_data=f"set_poll_{service_id}_4", style="primary")
        ],
        [
            InlineKeyboardButton(text="5-variant", callback_data=f"set_poll_{service_id}_5", style="primary"),
            InlineKeyboardButton(text="6-variant", callback_data=f"set_poll_{service_id}_6", style="primary")
        ],
        [
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="cancel_order", style="primary")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_order_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="confirm_order", style="primary")
        ],
        [
            InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="cancel_order", style="primary")
        ]
    ])

def get_referral_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏆 TOP 10 Foydalanuvchilar", callback_data="ref_top10", style="primary")
        ],
        [
            InlineKeyboardButton(text="🌐 Saytimiz", url=settings.WEBSITE_URL, style="primary")
        ]
    ])

def get_hisobim_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Balansni to'ldirish", callback_data="deposit_money", style="primary")
        ]
    ])

def get_payment_systems_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="CLICK", callback_data="pay_CLICK", style="primary"),
            InlineKeyboardButton(text="PAYME", callback_data="pay_PAYME", style="primary")
        ],
        [
            InlineKeyboardButton(text="UZUM", callback_data="pay_UZUM", style="primary"),
            InlineKeyboardButton(text="PAYNET", callback_data="pay_PAYNET", style="primary")
        ],
        [
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main", style="primary")
        ]
    ])

def get_payment_detail_keyboard(system: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ To'lov qildim (Chek yuborish)", callback_data=f"paid_{system}", style="primary")
        ],
        [
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data="deposit_money", style="primary")
        ]
    ])

def get_admin_payment_keyboard(payment_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_pay_appr_{payment_id}_{user_id}", style="primary"),
        ],
        [
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_pay_rej_{payment_id}_{user_id}", style="primary")
        ]
    ])

def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Balans qo'shish", callback_data="adm_add_bal", style="primary"),
            InlineKeyboardButton(text="📊 Statistika", callback_data="adm_stats", style="primary")
        ],
        [
            InlineKeyboardButton(text="📋 Audit jurnali", callback_data="adm_audit_logs", style="primary")
        ],
        [
            InlineKeyboardButton(text="📢 Kanallar ro'yxati", callback_data="adm_channels", style="primary")
        ]
    ])
