import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from loguru import logger
import uvicorn

import os
from bot.config import settings
from aiogram.client.session.aiohttp import AiohttpSession

# Setup proxy for PythonAnywhere free tier or custom proxy if configured
proxy_url = settings.PROXY_URL or os.environ.get("http_proxy") or os.environ.get("https_proxy")
if not proxy_url and os.path.exists("/home/Quvonch005") or "pythonanywhere" in os.environ.get("PYTHONANYWHERE_SITE", "").lower() or "pythonanywhere" in os.environ.get("USER", "").lower() or os.path.exists("/var/www"):
    proxy_url = "http://proxy.server:3128"

bot_session = AiohttpSession(proxy=proxy_url) if proxy_url else None

# Initialize Bot and Dispatcher
bot = Bot(token=settings.BOT_TOKEN or "MOCK_TOKEN", session=bot_session)
dp = Dispatcher(storage=MemoryStorage())

# Register Middlewares
dp.message.middleware(ThrottlingMiddleware(rate_limit=0.5))
dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.5))
dp.message.middleware(SubscriptionMiddleware())
dp.callback_query.middleware(SubscriptionMiddleware())

# Register Handlers
dp.include_router(start_router)
dp.include_router(admin_router)
dp.include_router(orders_router)
dp.include_router(payments_router)
dp.include_router(referral_router)
dp.include_router(main_menu_router)

polling_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global polling_task
    logger.info("Starting up Telegram Bot Application...")

    if settings.BOT_TOKEN and settings.BOT_TOKEN != "MOCK_TOKEN":
        # Configure "Saytimiz" Chat Menu Button
        try:
            from aiogram.types import MenuButtonWebApp, WebAppInfo
            if settings.WEBSITE_URL:
                await bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(
                        text="Saytimiz",
                        web_app=WebAppInfo(url=settings.WEBSITE_URL)
                    )
                )
        except Exception as e:
            logger.warning(f"Could not set chat menu button: {e}")

        if settings.WEBHOOK_URL:
            webhook_full_url = f"{settings.WEBHOOK_URL.rstrip('/')}{settings.WEBHOOK_PATH}"
            logger.info(f"Setting webhook to {webhook_full_url}")
            await bot.set_webhook(
                url=webhook_full_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            )
        else:
            logger.info("WEBHOOK_URL not provided. Starting in long-polling mode for local development...")
            await bot.delete_webhook(drop_pending_updates=True)
            polling_task = asyncio.create_task(dp.start_polling(bot, allowed_updates=["message", "callback_query"]))
    else:
        logger.warning("BOT_TOKEN is not configured or is default mock token.")

    yield

    logger.info("Shutting down Telegram Bot Application...")
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

    if settings.BOT_TOKEN and settings.BOT_TOKEN != "MOCK_TOKEN":
        try:
            await bot.delete_webhook()
        except Exception:
            pass
        await bot.session.close()

# FastAPI Webhook Application
app = FastAPI(title="Turfa Seen Telegram Bot", lifespan=lifespan)

@app.get("/health")
@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "Turfa Seen SMM Telegram Bot",
        "mode": "webhook" if settings.WEBHOOK_URL else "polling"
    }

@app.post(settings.WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error handling Telegram webhook update: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT
    )
