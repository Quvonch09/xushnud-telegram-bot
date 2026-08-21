import unittest
import asyncio
from bot.database import db
from bot.services import (
    settings_service,
    order_service,
    user_service,
    smm_provider
)
from bot.keyboards.reply import get_main_menu_keyboard, get_cancel_keyboard
from bot.keyboards.inline import (
    get_platforms_keyboard,
    get_categories_keyboard,
    get_services_keyboard,
    get_admin_main_keyboard,
    get_admin_card_keyboard,
    get_admin_start_msg_keyboard
)

class TestNewFeatures(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        db._mock_users.clear()
        db._mock_orders.clear()

    async def test_01_settings_service_card_and_welcome(self):
        # Test card change
        settings_service.set_card_number("8600 9999 8888 7777")
        self.assertEqual(settings_service.get_card_number(), "8600 9999 8888 7777")

        # Test comment change
        settings_service.set_card_comment("Ali Valiyev")
        self.assertEqual(settings_service.get_card_comment(), "Ali Valiyev")

        # Test custom welcome message
        settings_service.set_welcome_message("Salom, <b>{first_name}</b>! Botimizga xush kelibsiz.")
        msg = settings_service.get_welcome_message("Xushnud")
        self.assertEqual(msg, "Salom, <b>Xushnud</b>! Botimizga xush kelibsiz.")

        # Test reset welcome message
        settings_service.reset_welcome_message()
        self.assertIn("Turfa Seen", settings_service.get_welcome_message("Xushnud"))

    async def test_02_free_reaction_service(self):
        # Service ID 33 is "🎁 Tekin Reaksiya (50 tagacha)"
        service = await db.get_service_by_id(33)
        self.assertIsNotNone(service)
        self.assertEqual(service.price_per_1000, 0)
        self.assertTrue(service.is_free)
        self.assertEqual(service.min_order, 1)
        self.assertEqual(service.max_order, 50)
        self.assertTrue(service.requires_reaction)

        # Place free reaction order
        user, _ = await user_service.get_or_create_user(telegram_id=987654321)
        res = await order_service.validate_and_create_order(
            user_telegram_id=987654321,
            service_id=33,
            link="https://t.me/test_channel/99",
            quantity=50,
            reaction_type="🔥"
        )
        self.assertTrue(res["success"])
        order = res["order"]
        self.assertEqual(order.price, 0)
        self.assertEqual(order.reaction_type, "🔥")

    async def test_03_keyboards_and_icons(self):
        # Platform keyboard has Telegram, Instagram, YouTube, TikTok
        pkb = get_platforms_keyboard()
        buttons_text = [btn.text for row in pkb.inline_keyboard for btn in row]
        self.assertTrue(any("Telegram" in t for t in buttons_text))
        self.assertTrue(any("Instagram" in t for t in buttons_text))
        self.assertTrue(any("YouTube" in t for t in buttons_text))
        self.assertTrue(any("TikTok" in t for t in buttons_text))
        self.assertTrue(any("Asosiy menyu" in t for t in buttons_text))

        # Admin keyboards
        akb = get_admin_main_keyboard()
        admin_btns = [btn.text for row in akb.inline_keyboard for btn in row]
        self.assertTrue(any("Karta sozlamalari" in t for t in admin_btns))
        self.assertTrue(any("Start xabari" in t for t in admin_btns))
        self.assertTrue(any("Chiqish" in t for t in admin_btns))

        # Cancel keyboard
        ckb = get_cancel_keyboard()
        self.assertTrue(any("Bekor qilish" in btn.text for row in ckb.keyboard for btn in row))

if __name__ == "__main__":
    unittest.main()
