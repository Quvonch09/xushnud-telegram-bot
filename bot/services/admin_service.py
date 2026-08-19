from typing import Optional, List, Dict, Any
from loguru import logger
from bot.config import settings
from bot.database import db
from bot.database.models import OrderModel, AuditLogModel
from bot.services.audit_log import audit_service
from bot.services.order_service import order_service

class AdminService:
    """
    AdminService: Grants demo sandbox administration features strictly to authorized ADMIN_IDS.
    """
    @staticmethod
    def is_admin(telegram_id: int) -> bool:
        return telegram_id in settings.admin_ids

    async def get_demo_statistics(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        if not self.is_admin(telegram_id):
            logger.warning(f"[AdminService] Unauthorized access attempt by {telegram_id}")
            return None

        stats = await db.get_statistics()
        stats["is_demo_mode"] = True
        return stats

    async def get_audit_logs(self, telegram_id: int, limit: int = 50) -> Optional[List[AuditLogModel]]:
        if not self.is_admin(telegram_id):
            return None
        return await audit_service.get_logs(limit=limit)

    async def update_demo_order_status(
        self,
        telegram_id: int,
        order_id: int,
        new_status: str
    ) -> Optional[OrderModel]:
        if not self.is_admin(telegram_id):
            return None
        return await order_service.advance_order_status(order_id, new_status)


admin_service = AdminService()
