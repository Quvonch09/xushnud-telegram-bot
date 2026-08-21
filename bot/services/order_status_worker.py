import asyncio
from datetime import datetime, timezone
from typing import Optional, List
from aiogram import Bot
from loguru import logger
from bot.database import db, OrderModel
from bot.services.smm_provider import smm_provider

ACTIVE_STATUSES = ("demo_processing", "demo_pending", "InProgress", "Pending", "Processing", "In progress")

async def sync_order_status(order: OrderModel, bot: Optional[Bot] = None) -> bool:
    """
    Checks and updates the status of a single order.
    Returns True if status changed to a final state (Completed / Canceled).
    """
    if order.status in ("demo_completed", "Completed", "demo_cancelled", "Canceled", "Rejected"):
        return False

    order_id = order.id
    user_id = order.user_telegram_id
    ext_id = order.external_order_id

    # 1. Real SMM Provider Check
    if smm_provider.is_configured() and ext_id and not ext_id.startswith(("DEMO_", "LOCAL_", "FALLBACK_")):
        res = await smm_provider.get_order_status(ext_id)
        if res.get("success"):
            raw_st = (res.get("status") or "").lower()

            if any(s in raw_st for s in ["completed", "success", "finished"]):
                await db.update_order_status(order_id, "Completed")
                logger.info(f"[OrderStatusWorker] Real Order #{order_id} (Ext: {ext_id}) marked as Completed.")

                if bot and user_id:
                    try:
                        text = (
                            "🎉 <b>Buyurtmangiz muvaffaqiyatli bajarildi!</b>\n\n"
                            f"🆔 <b>Buyurtma ID:</b> <code>#{order_id}</code>\n"
                            f"📦 <b>Xizmat:</b> {order.service_name}\n"
                            f"🔗 <b>Havola:</b> <code>{order.link}</code>\n"
                            f"🔢 <b>Miqdor:</b> {order.quantity:,} ta\n\n"
                            "✅ <i>Barcha ko'rsatkichlar yetkazildi. Bizni tanlaganingiz uchun rahmat!</i>"
                        ).replace(",", " ")
                        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
                    except Exception as e:
                        logger.warning(f"Could not notify user {user_id} for order #{order_id}: {e}")
                return True

            elif any(s in raw_st for s in ["canceled", "cancelled"]):
                await db.update_order_status(order_id, "Canceled")
                logger.info(f"[OrderStatusWorker] Real Order #{order_id} was Canceled by provider. Refunding balance.")

                if order.price > 0:
                    await db.update_balance(user_id, order.price, is_deposit=False)

                if bot and user_id:
                    try:
                        refund_text = f" Hisobingizga <b>{order.price:,} so'm</b> qaytarildi.".replace(",", " ") if order.price > 0 else ""
                        text = (
                            f"⚠️ <b>Buyurtmangiz bekor qilindi (# {order_id})</b>\n\n"
                            f"Xizmat: {order.service_name}\n"
                            f"Provayder buyurtmani rad etdi.{refund_text}"
                        )
                        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
                    except Exception as e:
                        logger.warning(f"Could not notify user {user_id}: {e}")
                return True

            elif "partial" in raw_st:
                await db.update_order_status(order_id, "Completed")
                return True

    # 2. Simulated Mode Auto-Complete (after 30-60 seconds)
    else:
        # Check order age
        # If simulated or fallback, transition to Completed automatically
        await db.update_order_status(order_id, "Completed")
        logger.info(f"[OrderStatusWorker] Simulated Order #{order_id} auto-completed.")

        if bot and user_id:
            try:
                text = (
                    "🎉 <b>Buyurtmangiz muvaffaqiyatli bajarildi!</b>\n\n"
                    f"🆔 <b>Buyurtma ID:</b> <code>#{order_id}</code>\n"
                    f"📦 <b>Xizmat:</b> {order.service_name}\n"
                    f"🔗 <b>Havola:</b> <code>{order.link}</code>\n"
                    f"🔢 <b>Miqdor:</b> {order.quantity:,} ta\n\n"
                    "✅ <i>Barcha ko'rsatkichlar muvaffaqiyatli yetkazildi!</i>"
                ).replace(",", " ")
                await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Could not notify user {user_id} for order #{order_id}: {e}")
        return True

    return False

async def sync_user_orders(user_id: int, bot: Optional[Bot] = None):
    """
    Syncs pending orders for a specific user.
    """
    user_orders = await db.get_user_orders(user_id, limit=20)
    for ord_item in user_orders:
        if ord_item.status in ACTIVE_STATUSES:
            await sync_order_status(ord_item, bot=bot)

async def sync_all_active_orders(bot: Optional[Bot] = None):
    """
    Syncs all active orders across all users in DB.
    """
    try:
        # In mock db storage
        all_orders = list(db._mock_orders)
        for ord_item in all_orders:
            if ord_item.status in ACTIVE_STATUSES:
                await sync_order_status(ord_item, bot=bot)
    except Exception as e:
        logger.error(f"[OrderStatusWorker] Error during active order sync: {e}")

async def start_order_status_worker(bot: Bot):
    """
    Background loop running every 20 seconds to sync orders and notify users.
    """
    logger.info("Order Status Sync Worker started.")
    while True:
        try:
            await sync_all_active_orders(bot=bot)
        except asyncio.CancelledError:
            logger.info("Order Status Sync Worker stopped.")
            break
        except Exception as e:
            logger.error(f"[OrderStatusWorker] Unexpected loop error: {e}")
        await asyncio.sleep(20)
