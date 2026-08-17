from typing import Optional, List
from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel
from bot.database import db, OrderModel, PaymentModel
from bot.utils.telegram_auth import validate_telegram_init_data
from bot.config import settings

api_router = APIRouter(prefix="/api", tags=["Mini App API"])

class CreateOrderRequest(BaseModel):
    user_id: int
    platform: str
    category: str
    link: str
    quantity: int
    price: int

class CreateDepositRequest(BaseModel):
    user_id: int
    amount: int
    payment_system: Optional[str] = "Uzcard/Humo"

@api_router.get("/user")
async def get_user_data(
    user_id: int = Query(...),
    x_telegram_init_data: Optional[str] = Header(None)
):
    """
    Returns user profile, balance, and referral statistics.
    """
    # Verify initData if provided
    if x_telegram_init_data:
        validated = validate_telegram_init_data(x_telegram_init_data)
        if validated and "user" in validated:
            user_id = validated["user"].get("id", user_id)

    user = await db.get_user(user_id)
    if not user:
        user, _ = await db.create_or_get_user(telegram_id=user_id, username=f"user{user_id}", first_name="Foydalanuvchi")

    referrals = await db.get_user_referrals(user_id)
    ref_count = len(referrals)
    ref_earnings = ref_count * settings.REFERRAL_REWARD

    return {
        "user_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "balance": user.balance,
        "total_deposit": user.total_deposit,
        "referrals_count": ref_count,
        "referral_earnings": ref_earnings
    }

@api_router.get("/orders")
async def get_orders(
    user_id: int = Query(...),
    x_telegram_init_data: Optional[str] = Header(None)
):
    """
    Returns user's order history.
    """
    if x_telegram_init_data:
        validated = validate_telegram_init_data(x_telegram_init_data)
        if validated and "user" in validated:
            user_id = validated["user"].get("id", user_id)

    orders = await db.get_user_orders(user_id)
    return [
        {
            "id": o.id,
            "service_name": o.service_name,
            "quantity": o.quantity,
            "price": o.price,
            "status": o.status,
            "link": o.link,
            "created_at": str(o.created_at) if hasattr(o, "created_at") else ""
        }
        for o in orders
    ]

@api_router.post("/orders")
async def create_order(
    req: CreateOrderRequest,
    x_telegram_init_data: Optional[str] = Header(None)
):
    """
    Creates a new SMM order and deducts user balance.
    """
    user_id = req.user_id
    if x_telegram_init_data:
        validated = validate_telegram_init_data(x_telegram_init_data)
        if validated and "user" in validated:
            user_id = validated["user"].get("id", user_id)

    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    if user.balance < req.price:
        raise HTTPException(status_code=400, detail="Mablag' yetarli emas")

    # Deduct balance
    await db.update_user_balance(user_id, -req.price)

    # Save order
    order_data = OrderModel(
        user_id=user_id,
        service_id=0,
        service_name=f"{req.platform} - {req.category}",
        link=req.link,
        quantity=req.quantity,
        price=req.price,
        status="Pending"
    )
    new_order = await db.create_order(order_data)
    return {"status": "success", "order_id": new_order.id if new_order else 1}

@api_router.get("/account")
async def get_account(user_id: int = Query(...)):
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return {
        "telegram_id": user.telegram_id,
        "balance": user.balance,
        "total_deposit": user.total_deposit,
        "is_admin": user.telegram_id in settings.admin_ids
    }

@api_router.post("/deposit")
async def create_deposit(req: CreateDepositRequest):
    return {
        "status": "success",
        "card_number": settings.PAYMENT_CARD_NUMBER,
        "comment": settings.PAYMENT_COMMENT,
        "amount": req.amount
    }

@api_router.get("/referral")
async def get_referral(user_id: int = Query(...)):
    referrals = await db.get_user_referrals(user_id)
    return {
        "bot_username": settings.BOT_USERNAME,
        "referral_link": f"https://t.me/{settings.BOT_USERNAME}?start=user{user_id}",
        "reward_per_user": settings.REFERRAL_REWARD,
        "total_referrals": len(referrals),
        "total_earned": len(referrals) * settings.REFERRAL_REWARD
    }

@api_router.get("/help")
async def get_help():
    return {
        "support_admin": settings.SUPPORT_ADMIN,
        "official_channel": settings.OFFICIAL_CHANNEL,
        "website_url": settings.WEBSITE_URL or settings.WEBAPP_URL
    }
