from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Main Menu Reply Keyboard (2 columns, 4 rows)
    All buttons styled with style="primary" (bg_primary blue style).
    """
    keyboard = [
        [
            KeyboardButton(text="🛒 Buyurtma berish", style="primary"),
            KeyboardButton(text="📞 Raqam olish", style="primary")
        ],
        [
            KeyboardButton(text="👣 Buyurtmalar", style="primary"),
            KeyboardButton(text="🧑‍💼 Pul ishlash", style="primary")
        ],
        [
            KeyboardButton(text="💎 Hisobim", style="primary"),
            KeyboardButton(text="💳 Pul kiritish", style="primary")
        ],
        [
            KeyboardButton(text="❓ Yordam", style="primary"),
            KeyboardButton(text="💻 Hamkorlik dasturi", style="primary")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True
    )

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Cancel / Orqaga reply keyboard during FSM text inputs.
    """
    keyboard = [
        [KeyboardButton(text="❌ Bekor qilish", style="danger")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
