import uuid
import datetime
from typing import Dict, Any, Optional
from loguru import logger
from bot.database.models import PaymentModel

class DemoPaymentProvider:
    """
    DemoPaymentProvider: Safe local sandbox payment simulator.
    FEATURES:
    - Never charges real money.
    - Idempotency protection: same idempotency_key cannot be double-processed.
    - Deterministic responses for testing and UI demonstrations.
    """
    def __init__(self):
        self.provider_name = "DemoSandboxPaymentProvider"
        self._processed_transactions: Dict[str, Dict[str, Any]] = {}

    async def process_payment(
        self,
        user_telegram_id: int,
        amount: int,
        order_id: Optional[int] = None,
        system: str = "DEMO_PAY",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        key = idempotency_key or f"tx_{user_telegram_id}_{order_id}_{amount}"

        # Idempotency check: prevent double processing
        if key in self._processed_transactions:
            logger.warning(f"[DemoPaymentProvider] Idempotent hit: transaction {key} already processed!")
            return {
                "success": True,
                "test_paid": True,
                "is_duplicate": True,
                "transaction_id": self._processed_transactions[key]["transaction_id"],
                "message": "To'lov allaqachon qabul qilingan (Idempotent takrorlanish)."
            }

        tx_id = f"DEMO_TX_{uuid.uuid4().hex[:8].upper()}"
        record = {
            "transaction_id": tx_id,
            "user_telegram_id": user_telegram_id,
            "amount": amount,
            "order_id": order_id,
            "system": system,
            "test_paid": True,
            "is_demo": True,
            "status": "Approved",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self._processed_transactions[key] = record
        logger.info(f"[DemoPaymentProvider] Processed test payment {tx_id} for user {user_telegram_id}, amount {amount} so'm")

        return {
            "success": True,
            "test_paid": True,
            "is_duplicate": False,
            "transaction_id": tx_id,
            "amount": amount,
            "is_demo": True,
            "message": "✅ DEMO to'lov muvaffaqiyatli amalga oshirildi (Simulyatsiya)."
        }

    def is_processed(self, idempotency_key: str) -> bool:
        return idempotency_key in self._processed_transactions


demo_payment_provider = DemoPaymentProvider()
