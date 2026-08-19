import re
import uuid
import asyncio
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from loguru import logger

class MockProvider:
    """
    MockProvider: Safe local simulator for demo orders.
    STRICT BOUNDARIES:
    - NO external HTTP/API/socket requests.
    - NO engagement, botting, or real platform calls.
    - 100% deterministic local simulation for testing and UI demonstrations.
    """
    def __init__(self):
        self.provider_name = "LocalMockSandboxProvider"
        self._active_simulations: Dict[str, Dict[str, Any]] = {}

    def validate_url(self, link: str, platform: Optional[str] = None) -> tuple[bool, str]:
        """
        Validates URL syntax purely through offline regular expressions/urlparse.
        NEVER connects to the network or checks remote server.
        """
        if not link or not isinstance(link, str):
            return False, "Havola bo'sh bo'lishi mumkin emas."
        
        link = link.strip()
        if not (link.startswith("http://") or link.startswith("https://") or link.startswith("t.me/") or link.startswith("@")):
            return False, "Havola 'https://' yoki '@' bilan boshlanishi kerak (Masalan: https://t.me/kanal_nomi)."

        # Offline platform syntax checks
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
        """
        Simulates order creation locally with zero network calls.
        """
        mock_id = f"DEMO_ORD_{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"[MockProvider] Creating local simulated order: id={mock_id}, service={service_name}, qty={quantity}")

        sim_data = {
            "order_id": mock_id,
            "service_id": service_id,
            "service_name": service_name,
            "link": link,
            "quantity": quantity,
            "status": "demo_processing",
            "is_demo": True,
            "estimated_time": "1-5 daqiqa (Demo simulyatsiya)"
        }
        self._active_simulations[mock_id] = sim_data

        return {
            "success": True,
            "order_id": mock_id,
            "status": "demo_processing",
            "is_demo": True,
            "message": "DEMO MODE — Buyurtma muvaffaqiyatli simulyatsiya qilindi."
        }

    async def advance_status(self, external_order_id: str, new_status: str = "demo_completed") -> Optional[str]:
        """
        Advances the simulated order status locally.
        """
        if external_order_id in self._active_simulations:
            self._active_simulations[external_order_id]["status"] = new_status
            return new_status
        return new_status

    async def check_order_status(self, external_order_id: str) -> str:
        """
        Returns the current simulated status without making external calls.
        """
        if external_order_id in self._active_simulations:
            return self._active_simulations[external_order_id].get("status", "demo_completed")
        return "demo_completed"


mock_provider = MockProvider()
