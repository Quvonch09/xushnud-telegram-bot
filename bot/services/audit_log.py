import datetime
from typing import Optional, Dict, Any, List
from loguru import logger
from bot.database.models import AuditLogModel

class AuditLogService:
    """
    AuditLogService: Logs all sandbox demo actions (timestamp, user_id, order_id, action, details)
    purely for local diagnostic, auditing, and sandbox monitoring.
    """
    def __init__(self):
        self._logs: List[AuditLogModel] = []

    async def log_action(
        self,
        user_id: int,
        action: str,
        order_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLogModel:
        log_entry = AuditLogModel(
            id=len(self._logs) + 1,
            user_id=user_id,
            order_id=order_id,
            action=action,
            details=details or {},
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        self._logs.append(log_entry)
        logger.info(f"[AUDIT_LOG] user={user_id} action={action} order_id={order_id} details={details}")
        return log_entry

    async def get_logs(self, limit: int = 50) -> List[AuditLogModel]:
        return list(reversed(self._logs[-limit:]))

audit_service = AuditLogService()
