from typing import Optional, Tuple
from loguru import logger
from bot.database import db
from bot.database.models import UserModel
from bot.services.audit_log import audit_service

class UserService:
    """
    UserService: Manages demo user balances, profiles, and referral tracking.
    """
    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        referrer_id: Optional[int] = None
    ) -> Tuple[UserModel, bool]:
        user, is_new = await db.create_or_get_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            referrer_id=referrer_id
        )
        if is_new:
            await audit_service.log_action(
                user_id=telegram_id,
                action="REGISTER_DEMO_USER",
                details={"username": username, "first_name": first_name, "initial_balance": user.balance}
            )
        return user, is_new

    async def add_demo_balance(self, telegram_id: int, amount: int) -> bool:
        if amount <= 0:
            return False
        res = await db.update_balance(telegram_id, amount, is_deposit=True)
        if res:
            await audit_service.log_action(
                user_id=telegram_id,
                action="ADD_DEMO_BALANCE",
                details={"amount": amount}
            )
        return res

    async def get_user_profile(self, telegram_id: int) -> Optional[UserModel]:
        return await db.get_user(telegram_id)


user_service = UserService()
