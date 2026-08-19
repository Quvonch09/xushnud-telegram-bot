from typing import Optional, List
from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel
from bot.database import db, OrderModel, PaymentModel
from bot.services import order_service, mock_provider, user_service
from bot.utils.telegram_auth import validate_telegram_init_data
from bot.config import settings

api_router = APIRouter(prefix="/api", tags=["Mini App Sandbox API"])

class CreateOrderRequest(BaseModel):
    user_id: int
    platform: str
    category: str
    link: str
    quantity: int
    price: Optional[int] = None

class CreateDepositRequest(BaseModel):
    user_id: int
    amount: int
    payment_system: Optional[str] = "DemoPay"

@api_router.get("/user")
async def get_user_data(
    user_id: int = Query(...),
    x_telegram_init_data: Optional[str] = Header(None)
):
    """
    Returns user profile, demo balance, and referral statistics.
    """
    if x_telegram_init_data:
        validated = validate_telegram_init_data(x_telegram_init_data)
        if validated and "user" in validated:
            user_id = validated["user"].get("id", user_id)

    user = await db.get_user(user_id)
    if not user:
        user, _ = await db.create_or_get_user(telegram_id=user_id, username=f"user{user_id}", first_name="Foydalanuvchi")

    return {
        "user_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "balance": user.balance,
        "demo_balance": user.balance,
        "total_deposit": user.total_deposit,
        "referrals_count": user.referral_count,
        "referral_earnings": user.referral_count * settings.REFERRAL_REWARD,
        "is_demo": True
    }

@api_router.get("/orders")
async def get_orders(
    user_id: int = Query(...),
    x_telegram_init_data: Optional[str] = Header(None)
):
    """
    Returns user's demo order history.
    """
    if x_telegram_init_data:
        validated = validate_telegram_init_data(x_telegram_init_data)
        if validated and "user" in validated:
            user_id = validated["user"].get("id", user_id)

    orders = await order_service.get_user_orders(user_id, limit=20)
    return [
        {
            "id": o.id,
            "service_name": o.service_name,
            "quantity": o.quantity,
            "price": o.price,
            "status": o.status,
            "is_demo": True,
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
    Creates a new sandbox demo order via OrderService with server-side validation.
    """
    user_id = req.user_id
    if x_telegram_init_data:
        validated = validate_telegram_init_data(x_telegram_init_data)
        if validated and "user" in validated:
            user_id = validated["user"].get("id", user_id)

    services = await db.get_services_by_category(req.platform, req.category)
    service = services[0] if services else await db.get_service_by_id(1)
    if not service:
        raise HTTPException(status_code=404, detail="Demo xizmat topilmadi")

    res = await order_service.validate_and_create_order(
        user_telegram_id=user_id,
        service_id=service.id,
        link=req.link,
        quantity=req.quantity
    )

    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])

    order = res["order"]
    return {
        "status": "success",
        "order_id": order.id,
        "is_demo": True,
        "message": res["message"],
        "estimated_time": res["estimated_time"]
    }

@api_router.get("/account")
async def get_account(user_id: int = Query(...)):
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return {
        "telegram_id": user.telegram_id,
        "balance": user.balance,
        "demo_balance": user.balance,
        "total_deposit": user.total_deposit,
        "is_demo": True,
        "is_admin": user.telegram_id in settings.admin_ids
    }

@api_router.post("/deposit")
async def create_deposit(req: CreateDepositRequest):
    # In sandbox demo mode, immediately add demo balance
    await user_service.add_demo_balance(req.user_id, req.amount)
    return {
        "status": "success",
        "is_demo": True,
        "amount": req.amount,
        "message": "✅ Demo mablag' hisobingizga muvaffaqiyatli qo'shildi (Simulyatsiya)."
    }

@api_router.get("/referral")
async def get_referral(user_id: int = Query(...)):
    user = await db.get_user(user_id)
    ref_count = user.referral_count if user else 0
    return {
        "bot_username": settings.BOT_USERNAME,
        "referral_link": f"https://t.me/{settings.BOT_USERNAME}?start=user{user_id}",
        "reward_per_user": settings.REFERRAL_REWARD,
        "total_referrals": ref_count,
        "total_earned": ref_count * settings.REFERRAL_REWARD,
        "is_demo": True
    }

@api_router.get("/help")
async def get_help():
    return {
        "support_admin": settings.SUPPORT_ADMIN,
        "official_channel": settings.OFFICIAL_CHANNEL,
        "website_url": settings.WEBSITE_URL or settings.WEBAPP_URL,
        "is_demo": True,
        "notice": "DEMO MODE — Faqat test simulyatsiyasi uchun."
    }
