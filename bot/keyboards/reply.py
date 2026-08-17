from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Main Menu Reply Keyboard (2 columns, 4 rows)
    Matches 100% exact layout and icons from screenshots.
    """
    keyboard = [
        [
            KeyboardButton(text="🛒 Buyurtma berish"),
            KeyboardButton(text="📞 Raqam olish")
        ],
        [
            KeyboardButton(text="🐾 Buyurtmalar"),
            KeyboardButton(text="🐥 Pul ishlash")
        ],
        [
            KeyboardButton(text="💎 Hisobim"),
            KeyboardButton(text="💳 Pul kiritish")
        ],
        [
            KeyboardButton(text="? Yordam"),
            KeyboardButton(text="💻 Hamkorlik dasturi")
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
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
