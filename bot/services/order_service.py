import math
from typing import Optional, List, Dict, Any
from loguru import logger
from bot.database import db
from bot.database.models import OrderModel, ServiceModel, UserModel
from bot.services.mock_provider import mock_provider
from bot.services.demo_payment_provider import demo_payment_provider
from bot.services.audit_log import audit_service

class OrderService:
    """
    OrderService: Manages lifecycle, validation, server-side price calculation,
    and history of sandbox demo orders.
    """
    @staticmethod
    def calculate_price(service: ServiceModel, quantity: int) -> int:
        if service.is_free or service.price_per_1000 == 0:
            return 0
        return int(math.ceil((quantity * service.price_per_1000) / 1000.0))

    async def validate_and_create_order(
        self,
        user_telegram_id: int,
        service_id: int,
        link: str,
        quantity: int,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        # 1. Fetch Service
        service = await db.get_service_by_id(service_id)
        if not service:
            return {"success": False, "error": "Tanlangan xizmat topilmadi."}

        # 2. Validate URL syntax (offline)
        valid_url, url_err = mock_provider.validate_url(link, service.platform)
        if not valid_url:
            return {"success": False, "error": url_err}

        # 3. Validate Quantity limits
        if not isinstance(quantity, int) or quantity <= 0:
            return {"success": False, "error": "Miqdor musbat butun son bo'lishi kerak."}

        if quantity < service.min_order:
            return {"success": False, "error": f"Minimal buyurtma miqdori: {service.min_order:,} ta".replace(",", " ")}

        if quantity > service.max_order:
            return {"success": False, "error": f"Maksimal buyurtma miqdori: {service.max_order:,} ta".replace(",", " ")}

        # 4. Calculate Server Price (Never trust client price)
        price = self.calculate_price(service, quantity)

        # 5. Check User Demo Balance
        user = await db.get_user(user_telegram_id)
        if not user:
            user, _ = await db.create_or_get_user(user_telegram_id)

        if user.balance < price:
            deficit = price - user.balance
            return {
                "success": False,
                "error": f"Mablag' yetarli emas! Sizda: {user.balance:,} so'm, kerak: {price:,} so'm (Yetishmayapti: {deficit:,} so'm).".replace(",", " "),
                "need_deposit": True,
                "price": price,
                "balance": user.balance
            }

        # 6. Process Demo Payment with Idempotency
        key = idempotency_key or f"order_{user_telegram_id}_{service_id}_{quantity}_{link}"
        if demo_payment_provider.is_processed(key):
            return {"success": False, "error": "Ushbu buyurtma to'lovi allaqachon bajarilgan."}

        # Deduct balance
        if price > 0:
            await db.update_balance(user_telegram_id, -price, is_deposit=False)

        pay_res = await demo_payment_provider.process_payment(
            user_telegram_id=user_telegram_id,
            amount=price,
            system="DEMO_BALANCE",
            idempotency_key=key
        )

        # 7. Create Demo Provider Order (Zero network calls)
        mock_res = await mock_provider.create_demo_order(
            service_id=service.id,
            service_name=service.name,
            link=link,
            quantity=quantity
        )

        # 8. Save Order in Database with is_demo=True strictly
        order = await db.create_order(
            user_telegram_id=user_telegram_id,
            service_id=service.id,
            service_name=f"{service.platform} - {service.name} (DEMO)",
            link=link,
            quantity=quantity,
            price=price,
            external_order_id=mock_res["order_id"],
            status="demo_processing",
            estimated_time=service.estimated_time or "1-5 daqiqa (Demo)"
        )

        # 9. Audit Log
        await audit_service.log_action(
            user_id=user_telegram_id,
            action="CREATE_DEMO_ORDER",
            order_id=order.id,
            details={
                "service": service.name,
                "platform": service.platform,
                "quantity": quantity,
                "price": price,
                "is_demo": True
            }
        )

        return {
            "success": True,
            "order": order,
            "price": price,
            "estimated_time": service.estimated_time or "1-5 daqiqa (Demo)",
            "message": "✅ Demo buyurtma yaratildi. Bu buyurtma hech qanday tashqi platformaga yuborilmaydi."
        }

    async def get_user_orders(self, user_telegram_id: int, limit: int = 10) -> List[OrderModel]:
        return await db.get_user_orders(user_telegram_id, limit=limit)

    async def advance_order_status(self, order_id: int, new_status: str) -> Optional[OrderModel]:
        valid_statuses = ["demo_pending", "demo_paid", "demo_processing", "demo_completed", "demo_cancelled"]
        if new_status not in valid_statuses:
            return None
        updated = await db.update_order_status(order_id, new_status)
        if updated:
            await audit_service.log_action(
                user_id=updated.user_telegram_id,
                action=f"UPDATE_ORDER_STATUS_TO_{new_status.upper()}",
                order_id=order_id,
                details={"status": new_status, "is_demo": True}
            )
        return updated


order_service = OrderService()
