from bot.handlers.start import start_router
from bot.handlers.main_menu import main_menu_router
from bot.handlers.orders import orders_router
from bot.handlers.payments import payments_router
from bot.handlers.referral import referral_router
from bot.handlers.admin import admin_router

__all__ = [
    "start_router",
    "main_menu_router",
    "orders_router",
    "payments_router",
    "referral_router",
    "admin_router"
]
