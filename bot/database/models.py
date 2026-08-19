from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class UserModel(BaseModel):
    id: Optional[int] = None
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    balance: int = 50000  # Default 50 000 demo UZS for instant sandbox testing
    total_deposit: int = 0
    referral_id: Optional[int] = None
    referral_count: int = 0
    is_banned: bool = False
    is_demo: bool = True
    created_at: Optional[str] = None

    @property
    def demo_balance(self) -> int:
        return self.balance


class ChannelModel(BaseModel):
    id: int
    name: str
    link: str
    username: Optional[str] = None
    is_active: bool = True


class ServiceModel(BaseModel):
    id: int
    platform: str  # Telegram, Instagram, YouTube, TikTok
    category: str  # Reaksiya, Ko'rishlar, Obunachi, Boost ovoz, Hikoya, O'zbek tarmoq, Ovozlar, Boostlar
    service_id_external: Optional[int] = None
    name: str
    price_per_1000: int
    min_order: int = 10
    max_order: int = 100000
    description: Optional[str] = "Faqat ommaviy kanal va postlar uchun ishlaydi"
    estimated_time: str = "1-5 daqiqa"
    is_free: bool = False
    is_demo: bool = True
    requires_reaction: bool = False
    requires_poll_option: bool = False


class OrderModel(BaseModel):
    id: Optional[int] = None
    user_telegram_id: int
    service_id: Optional[int] = None
    service_name: Optional[str] = None
    link: str
    quantity: int
    price: int
    status: str = "demo_processing"  # demo_pending, demo_paid, demo_processing, demo_completed, demo_cancelled, Pending, InProgress, Completed, Canceled
    estimated_time: Optional[str] = "1-5 daqiqa (Demo)"
    reaction_type: Optional[str] = None
    poll_option: Optional[str] = None
    extra_params: Optional[Dict[str, Any]] = None
    is_demo: bool = True
    external_order_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PaymentModel(BaseModel):
    id: Optional[int] = None
    user_telegram_id: int
    order_id: Optional[int] = None
    system: str = "DEMO_PAY"
    provider: str = "DemoPaymentProvider"
    amount: Optional[int] = None
    card_number: Optional[str] = "8600 **** **** 1234 (DEMO)"
    comment: Optional[str] = "DEMO_PAYMENT"
    screenshot_file_id: Optional[str] = None
    status: str = "Approved"
    is_demo: bool = True
    created_at: Optional[str] = None


class ReferralModel(BaseModel):
    id: Optional[int] = None
    referrer_id: int
    referred_id: int
    reward: int = 80
    is_demo: bool = True
    created_at: Optional[str] = None


class AuditLogModel(BaseModel):
    id: Optional[int] = None
    user_id: int
    order_id: Optional[int] = None
    action: str
    details: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
