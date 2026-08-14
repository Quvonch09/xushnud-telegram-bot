from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class UserModel(BaseModel):
    id: Optional[int] = None
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    balance: int = 0
    total_deposit: int = 0
    referral_id: Optional[int] = None
    referral_count: int = 0
    is_banned: bool = False
    created_at: Optional[str] = None

class ChannelModel(BaseModel):
    id: int
    name: str
    link: str
    username: Optional[str] = None
    is_active: bool = True

class ServiceModel(BaseModel):
    id: int
    platform: str
    category: str
    service_id_external: Optional[int] = None
    name: str
    price_per_1000: int
    min_order: int
    max_order: int
    description: Optional[str] = None
    is_free: bool = False

class OrderModel(BaseModel):
    id: Optional[int] = None
    user_telegram_id: int
    service_id: Optional[int] = None
    service_name: Optional[str] = None
    link: str
    quantity: int
    price: int
    status: str = "Pending"
    external_order_id: Optional[str] = None
    created_at: Optional[str] = None

class PaymentModel(BaseModel):
    id: Optional[int] = None
    user_telegram_id: int
    system: str
    amount: Optional[int] = None
    card_number: Optional[str] = "5614684605929718"
    comment: Optional[str] = "8048583227"
    screenshot_file_id: Optional[str] = None
    status: str = "Pending"
    created_at: Optional[str] = None

class ReferralModel(BaseModel):
    id: Optional[int] = None
    referrer_id: int
    referred_id: int
    reward: int = 80
    created_at: Optional[str] = None
