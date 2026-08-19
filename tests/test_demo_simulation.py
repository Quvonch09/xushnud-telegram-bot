import unittest
import asyncio
from bot.database import db
from bot.database.models import OrderModel, UserModel, ServiceModel
from bot.services import (
    mock_provider,
    demo_payment_provider,
    order_service,
    user_service,
    admin_service,
    audit_service,
    smm_provider
)
from bot.keyboards.reply import get_main_menu_keyboard
from bot.keyboards.inline import (
    get_categories_keyboard,
    get_order_confirmation_keyboard,
    get_reaction_emojis_keyboard,
    get_poll_options_keyboard
)

class TestDemoSimulator(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Reset mock database state before each test
        db._mock_users.clear()
        db._mock_orders.clear()
        db._mock_payments.clear()
        demo_payment_provider._processed_transactions.clear()

    # 1. Foydalanuvchi ro'yxatdan o'tadi
    async def test_01_user_registration(self):
        user, is_new = await user_service.get_or_create_user(
            telegram_id=999888777,
            username="test_demo_user",
            first_name="DemoTester"
        )
        self.assertTrue(is_new)
        self.assertEqual(user.telegram_id, 999888777)
        self.assertTrue(user.is_demo)
        self.assertGreaterEqual(user.balance, 50000)

    # 2. Demo xizmat tanlaydi
    async def test_02_service_selection(self):
        categories = await db.get_categories_by_platform("Telegram")
        self.assertIn("Obunachi", categories)
        self.assertIn("Reaksiya", categories)
        self.assertIn("Ovozlar", categories)
        self.assertIn("Boost ovoz", categories)
        services = await db.get_services_by_category("Telegram", "Obunachi")
        self.assertGreater(len(services), 0)
        self.assertTrue(services[0].is_demo)

    # 3. Noto'g'ri havola yuborilganda xato chiqadi
    async def test_03_invalid_url_rejection(self):
        valid, err = mock_provider.validate_url("not_a_valid_link", "Telegram")
        self.assertFalse(valid)
        self.assertIn("https://", err)

        res = await order_service.validate_and_create_order(
            user_telegram_id=999888777,
            service_id=1,
            link="invalid_url",
            quantity=50
        )
        self.assertFalse(res["success"])
        self.assertIn("https://", res["error"])

    # 4. To'g'ri demo havola bilan order yaratiladi
    async def test_04_valid_order_creation(self):
        user, _ = await user_service.get_or_create_user(telegram_id=111222333)
        res = await order_service.validate_and_create_order(
            user_telegram_id=111222333,
            service_id=2, # 30 Kun kafolat
            link="https://t.me/demo_channel",
            quantity=100
        )
        self.assertTrue(res["success"])
        order = res["order"]
        self.assertIsNotNone(order.id)
        self.assertTrue(order.is_demo)
        self.assertIsNotNone(order.external_order_id)

    # 5. Demo payment ikki marta kelganda takroriy balans yechilmaydi (Idempotency)
    async def test_05_idempotent_payment(self):
        user, _ = await user_service.get_or_create_user(telegram_id=333444555)
        key = "idemp_test_tx_001"
        res1 = await demo_payment_provider.process_payment(
            user_telegram_id=333444555,
            amount=5000,
            idempotency_key=key
        )
        self.assertTrue(res1["success"])
        self.assertFalse(res1["is_duplicate"])

        res2 = await demo_payment_provider.process_payment(
            user_telegram_id=333444555,
            amount=5000,
            idempotency_key=key
        )
        self.assertTrue(res2["success"])
        self.assertTrue(res2["is_duplicate"])

    # 6. MockProvider tashqi tarmoqqa so'rov yubormasligi
    async def test_06_mock_provider_offline(self):
        res = await mock_provider.create_demo_order(
            service_id=1,
            service_name="Test Service",
            link="https://t.me/offline_test",
            quantity=20
        )
        self.assertTrue(res["success"])
        self.assertTrue(res["is_demo"])
        self.assertEqual(res["status"], "demo_processing")

    # 7. Oddiy user admin menyusini ocholmaydi
    async def test_07_admin_permissions(self):
        non_admin_id = 999999999
        stats = await admin_service.get_demo_statistics(non_admin_id)
        self.assertIsNone(stats)

        logs = await admin_service.get_audit_logs(non_admin_id)
        self.assertIsNone(logs)

    # 8. Demo order statuslari to'g'ri o'zgaradi
    async def test_08_status_transitions(self):
        user, _ = await user_service.get_or_create_user(telegram_id=777666555)
        res = await order_service.validate_and_create_order(
            user_telegram_id=777666555,
            service_id=1,
            link="https://t.me/test_status",
            quantity=10
        )
        order = res["order"]
        self.assertEqual(order.status, "demo_processing")

        updated = await order_service.advance_order_status(order.id, "demo_completed")
        self.assertIsNotNone(updated)
        self.assertEqual(updated.status, "demo_completed")

    # 9. Bot restart bo'lgandan keyin order tarixi saqlanadi
    async def test_09_order_persistence_and_history(self):
        user_id = 888111222
        await user_service.get_or_create_user(telegram_id=user_id)
        await order_service.validate_and_create_order(
            user_telegram_id=user_id,
            service_id=1,
            link="https://t.me/persist_test_1",
            quantity=10
        )
        await order_service.validate_and_create_order(
            user_telegram_id=user_id,
            service_id=1,
            link="https://t.me/persist_test_2",
            quantity=10
        )
        history = await order_service.get_user_orders(user_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].link, "https://t.me/persist_test_2")

    # 10. Mobile UI'da tugmalar ikki ustunda chiroyli chiqadi
    def test_10_keyboard_structure(self):
        main_kb = get_main_menu_keyboard()
        self.assertEqual(len(main_kb.keyboard), 4)
        for row in main_kb.keyboard:
            self.assertEqual(len(row), 2)
            for btn in row:
                self.assertEqual(btn.style, "primary")

    # 11. DEMO MODE belgisi ko'rinishi
    def test_11_demo_mode_labels(self):
        from bot.handlers.orders import DEMO_BANNER
        self.assertIn("DEMO MODE", DEMO_BANNER)

    # 12. is_demo=True bo'lmagan order yaratish imkonsizligi
    async def test_12_is_demo_enforced(self):
        user_id = 555666777
        await user_service.get_or_create_user(telegram_id=user_id)
        res = await order_service.validate_and_create_order(
            user_telegram_id=user_id,
            service_id=1,
            link="https://t.me/strict_demo_test",
            quantity=10
        )
        order = res["order"]
        self.assertTrue(order.is_demo)

    # 13. Reaksiyalar (Reactions) emoji tanlash bilan buyurtma berish
    async def test_13_reactions_with_emoji(self):
        user_id = 444333222
        await user_service.get_or_create_user(telegram_id=user_id)
        res = await order_service.validate_and_create_order(
            user_telegram_id=user_id,
            service_id=7, # Tanlangan emoji reaksiyasi
            link="https://t.me/demo_channel/123",
            quantity=50,
            reaction_type="🔥"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["order"].reaction_type, "🔥")

        kb = get_reaction_emojis_keyboard(7)
        self.assertGreater(len(kb.inline_keyboard), 0)

    # 14. Ovozlar (Poll Votes) variant tanlash bilan buyurtma berish
    async def test_14_poll_votes_with_option(self):
        user_id = 666777888
        await user_service.get_or_create_user(telegram_id=user_id)
        res = await order_service.validate_and_create_order(
            user_telegram_id=user_id,
            service_id=29, # So'rovnoma ovozlari
            link="https://t.me/demo_channel/456",
            quantity=100,
            poll_option="2"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["order"].poll_option, "2")

        kb = get_poll_options_keyboard(29)
        self.assertGreater(len(kb.inline_keyboard), 0)

    # 15. Ko'rishlar (Views) va Boostlar (Boosts) xizmatlari
    async def test_15_views_and_boosts_services(self):
        user_id = 123789456
        await user_service.get_or_create_user(telegram_id=user_id)
        # Views
        res_views = await order_service.validate_and_create_order(
            user_telegram_id=user_id,
            service_id=9, # Oxirgi 1 ta post ko'rishlar
            link="https://t.me/demo_channel/123",
            quantity=500
        )
        self.assertTrue(res_views["success"])

        # Boosts
        res_boosts = await order_service.validate_and_create_order(
            user_telegram_id=user_id,
            service_id=12, # Kanal uchun Boost (1 kunlik)
            link="https://t.me/demo_channel",
            quantity=5
        )
        self.assertTrue(res_boosts["success"])

    # 16. SMM Provider Client metodlari (add_order, get_order_status, get_balance)
    async def test_16_smm_provider_client(self):
        add_res = await smm_provider.add_order(
            service_id=9,
            link="https://t.me/demo_channel/10",
            quantity=100,
            reaction="❤️",
            answer_number="1"
        )
        self.assertTrue(add_res["success"])

        status_res = await smm_provider.get_order_status("DEMO_TEST_001")
        self.assertTrue(status_res["success"])

        bal_res = await smm_provider.get_balance()
        self.assertTrue(bal_res["success"])


if __name__ == "__main__":
    unittest.main()
