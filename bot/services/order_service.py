import math
from typing import Optional, List, Dict, Any
from loguru import logger
from bot.database import db
from bot.database.models import OrderModel, ServiceModel, UserModel
from bot.services.smm_provider import smm_provider
from bot.services.mock_provider import mock_provider
from bot.services.demo_payment_provider import demo_payment_provider
from bot.services.audit_log import audit_service

class OrderService:
    """
    OrderService: Manages lifecycle, validation, server-side price calculation,
    and history of orders (supporting Views, Reactions, Poll Votes, and Boosts).
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
        reaction_type: Optional[str] = None,
        poll_option: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        # 1. Fetch Service
        service = await db.get_service_by_id(service_id)
        if not service:
            return {"success": False, "error": "Tanlangan xizmat topilmadi."}

        # 2. Validate URL syntax
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

        # 5. Check User Balance
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

        # 6. Process Payment with Idempotency
        key = idempotency_key or f"order_{user_telegram_id}_{service_id}_{quantity}_{link}_{reaction_type}_{poll_option}"
        if demo_payment_provider.is_processed(key):
            return {"success": False, "error": "Ushbu buyurtma to'lovi allaqachon bajarilgan."}

        # Deduct balance temporarily
        if price > 0:
            await db.update_balance(user_telegram_id, -price, is_deposit=False)

        pay_res = await demo_payment_provider.process_payment(
            user_telegram_id=user_telegram_id,
            amount=price,
            system="BALANCE",
            idempotency_key=key
        )

        # 7. Create Provider Order (SMM v2 API client or fallback)
        provider_res = await smm_provider.add_order(
            service_id=service.service_id_external or service.id,
            link=link,
            quantity=quantity,
            service_name=service.name,
            reaction=reaction_type,
            answer_number=poll_option,
            **(extra_params or {})
        )

        if not provider_res.get("success"):
            # REFUND balance on provider failure
            if price > 0:
                await db.update_balance(user_telegram_id, price, is_deposit=False)
                logger.warning(f"[OrderService] Refunded {price} so'm to user {user_telegram_id} due to provider error.")

            await audit_service.log_action(
                user_id=user_telegram_id,
                action="ORDER_FAILED_REFUNDED",
                details={"service": service.name, "price": price, "error": provider_res.get("error")}
            )
            return {
                "success": False,
                "error": f"Provayder xatoligi: {provider_res.get('error', 'Nomaʼlum xatolik')}. Mablag'ingiz hisobingizga qaytarildi."
            }

        import uuid
        ext_id = provider_res.get("order_id") or f"ORD_{uuid.uuid4().hex[:8].upper()}"
        status = provider_res.get("status", "InProgress")
        is_demo_flag = provider_res.get("is_demo", False)

        # 8. Save Order in Database
        order = await db.create_order(
            user_telegram_id=user_telegram_id,
            service_id=service.id,
            service_name=f"{service.platform} - {service.name}",
            link=link,
            quantity=quantity,
            price=price,
            external_order_id=ext_id,
            status=status,
            estimated_time=service.estimated_time or "1-5 daqiqa"
        )
        order.is_demo = is_demo_flag
        order.reaction_type = reaction_type
        order.poll_option = poll_option
        order.extra_params = extra_params

        # 9. Audit Log
        await audit_service.log_action(
            user_id=user_telegram_id,
            action="CREATE_ORDER",
            order_id=order.id,
            details={
                "service": service.name,
                "platform": service.platform,
                "quantity": quantity,
                "price": price,
                "reaction_type": reaction_type,
                "poll_option": poll_option,
                "is_demo": order.is_demo
            }
        )

        return {
            "success": True,
            "order": order,
            "price": price,
            "estimated_time": service.estimated_time or "1-5 daqiqa",
            "message": "✅ Buyurtma muvaffaqiyatli qabul qilindi va ishga tushirildi."
        }

    async def get_user_orders(self, user_telegram_id: int, limit: int = 10) -> List[OrderModel]:
        return await db.get_user_orders(user_telegram_id, limit=limit)

    async def advance_order_status(self, order_id: int, new_status: str) -> Optional[OrderModel]:
        valid_statuses = [
            "demo_pending", "demo_paid", "demo_processing", "demo_completed", "demo_cancelled",
            "Pending", "InProgress", "Completed", "Canceled"
        ]
        if new_status not in valid_statuses:
            return None
        updated = await db.update_order_status(order_id, new_status)
        if updated:
            await audit_service.log_action(
                user_id=updated.user_telegram_id,
                action=f"UPDATE_ORDER_STATUS_TO_{new_status.upper()}",
                order_id=order_id,
                details={"status": new_status, "is_demo": updated.is_demo}
            )
        return updated


order_service = OrderService()
