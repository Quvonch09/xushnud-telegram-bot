import re
import uuid
import asyncio
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from loguru import logger

class MockProvider:
    """
    MockProvider: Safe simulator when external API key is not yet configured.
    """
    def __init__(self):
        self.provider_name = "LocalMockSandboxProvider"
        self._active_simulations: Dict[str, Dict[str, Any]] = {}

    def validate_url(self, link: str, platform: Optional[str] = None) -> tuple[bool, str]:
        if not link or not isinstance(link, str):
            return False, "Havola bo'sh bo'lishi mumkin emas."
        
        link = link.strip()
        if not (link.startswith("http://") or link.startswith("https://") or link.startswith("t.me/") or link.startswith("@")):
            return False, "Havola 'https://' yoki '@' bilan boshlanishi kerak (Masalan: https://t.me/kanal_nomi)."

        if platform:
            plat = platform.lower()
            if "telegram" in plat:
                if not any(k in link for k in ["t.me/", "telegram.me/", "@"]):
                    return False, "Telegram uchun to'g'ri havola yuboring (Masalan: https://t.me/kanal_nomi yoki @kanal_nomi)."
            elif "instagram" in plat:
                if "instagram.com" not in link and not link.startswith("@"):
                    return False, "Instagram uchun to'g'ri havola yuboring (Masalan: https://instagram.com/username)."
            elif "youtube" in plat:
                if not any(k in link for k in ["youtube.com", "youtu.be"]):
                    return False, "YouTube uchun to'g'ri havola yuboring (Masalan: https://youtube.com/watch?v=...)."
            elif "tiktok" in plat:
                if "tiktok.com" not in link and not link.startswith("@"):
                    return False, "TikTok uchun to'g'ri havola yuboring (Masalan: https://tiktok.com/@username)."

        return True, "OK"

    async def create_demo_order(
        self,
        service_id: int,
        service_name: str,
        link: str,
        quantity: int
    ) -> Dict[str, Any]:
        mock_id = f"ORD_{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"[MockProvider] Order created: id={mock_id}, service={service_name}, qty={quantity}")

        sim_data = {
            "order_id": mock_id,
            "service_id": service_id,
            "service_name": service_name,
            "link": link,
            "quantity": quantity,
            "status": "InProgress",
            "is_demo": False,
            "estimated_time": "1-5 daqiqa"
        }
        self._active_simulations[mock_id] = sim_data

        return {
            "success": True,
            "order_id": mock_id,
            "status": "InProgress",
            "is_demo": False,
            "message": "Buyurtma muvaffaqiyatli qabul qilindi."
        }

    async def advance_status(self, external_order_id: str, new_status: str = "Completed") -> Optional[str]:
        if external_order_id in self._active_simulations:
            self._active_simulations[external_order_id]["status"] = new_status
            return new_status
        return new_status

    async def check_order_status(self, external_order_id: str) -> str:
        if external_order_id in self._active_simulations:
            return self._active_simulations[external_order_id].get("status", "InProgress")
        return "InProgress"


mock_provider = MockProvider()
