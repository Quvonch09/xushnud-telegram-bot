import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from loguru import logger
import uvicorn

from bot.config import settings
from aiogram.client.session.aiohttp import AiohttpSession
from bot.handlers import (
    start_router,
    main_menu_router,
    orders_router,
    payments_router,
    referral_router,
    admin_router
)
from bot.api import api_router
from bot.middlewares import ThrottlingMiddleware, SubscriptionMiddleware

# Setup proxy for PythonAnywhere free tier or custom proxy if configured
proxy_url = settings.PROXY_URL or os.environ.get("http_proxy") or os.environ.get("https_proxy")
if not proxy_url and (os.path.exists("/home/Quvonch005") or "pythonanywhere" in os.environ.get("PYTHONANYWHERE_SITE", "").lower() or "pythonanywhere" in os.environ.get("USER", "").lower() or os.path.exists("/var/www")):
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
    logger.info("Starting up Telegram Bot & Mini App Server...")

    if settings.BOT_TOKEN and settings.BOT_TOKEN != "MOCK_TOKEN":
        # Configure Telegram Menu Button for Mini App
        try:
            from aiogram.types import MenuButtonWebApp, WebAppInfo
            webapp_url = settings.effective_webapp_url
            if webapp_url:
                await bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(
                        text="🚀 Ilova",
                        web_app=WebAppInfo(url=webapp_url)
                    )
                )
                logger.info(f"Chat menu button configured for Mini App: {webapp_url}")
        except Exception as e:
            logger.warning(f"Could not set chat menu button: {e}")

        if settings.WEBHOOK_URL:
            webhook_full_url = f"{settings.WEBHOOK_URL.rstrip('/')}{settings.WEBHOOK_PATH}"
            logger.info(f"Setting webhook to {webhook_full_url}")
            await bot.set_webhook(
                url=webhook_full_url,
                drop_pending_updates=False,
                allowed_updates=dp.resolve_used_update_types()
            )
            webhook_info = await bot.get_webhook_info()
            logger.info(f"Telegram Webhook info: {webhook_info}")
        else:
            logger.info("WEBHOOK_URL not provided. Starting in long-polling mode for local development...")
            await bot.delete_webhook(drop_pending_updates=True)
            polling_task = asyncio.create_task(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))
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

# FastAPI Web Application
app = FastAPI(title="Turfa Seen Telegram Bot & Mini App", lifespan=lifespan)

# Enable CORS for Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Mount Static Files for Telegram Mini App
webapp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webapp")
if os.path.exists(webapp_dir):
    app.mount("/webapp", StaticFiles(directory=webapp_dir, html=True), name="webapp")
    app.mount("/static", StaticFiles(directory=webapp_dir), name="static")

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Turfa Seen SMM Telegram Bot & Mini App",
        "mode": "webhook" if settings.WEBHOOK_URL else "polling",
        "webapp_url": settings.effective_webapp_url
    }

@app.api_route("/", methods=["GET", "HEAD"])
async def serve_root():
    index_path = os.path.join(webapp_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "status": "healthy",
        "service": "Turfa Seen SMM Telegram Bot",
        "mode": "webhook" if settings.WEBHOOK_URL else "polling"
    }

@app.get("/webhook-info")
async def get_tg_webhook_info():
    """
    Diagnostic endpoint to check Telegram webhook status.
    """
    if settings.BOT_TOKEN and settings.BOT_TOKEN != "MOCK_TOKEN":
        info = await bot.get_webhook_info()
        return {
            "url": info.url,
            "has_custom_certificate": info.has_custom_certificate,
            "pending_update_count": info.pending_update_count,
            "last_error_date": info.last_error_date,
            "last_error_message": info.last_error_message,
            "max_connections": info.max_connections,
            "ip_address": info.ip_address
        }
    return {"error": "Bot token not configured"}

@app.post(settings.WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"Incoming Telegram webhook update: {data.get('update_id')}")
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error handling Telegram webhook update: {e}", exc_info=True)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT
    )


