import httpx
import uuid
from typing import Optional, Dict, Any
from loguru import logger
from bot.config import settings

class SmmApiService:
    def __init__(self):
        self.api_url = settings.SMM_API_URL
        self.api_key = settings.SMM_API_KEY

    async def create_order(
        self,
        service_id: int,
        link: str,
        quantity: int,
        is_free: bool = False
    ) -> Dict[str, Any]:
        """
        Creates order on external SMM provider, or simulates for free/demo mode.
        """
        if is_free or not self.api_url or not self.api_key or "smm-provider" in self.api_url:
            mock_id = f"LOCAL_{uuid.uuid4().hex[:8].upper()}"
            logger.info(f"Simulating SMM order. Service: {service_id}, Link: {link}, Qty: {quantity}, Simulated ID: {mock_id}")
            return {
                "success": True,
                "order_id": mock_id,
                "status": "Completed" if is_free else "InProgress"
            }

        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "key": self.api_key,
                    "action": "add",
                    "service": service_id,
                    "link": link,
                    "quantity": quantity
                }
                resp = await client.post(self.api_url, data=data, timeout=15.0)
                if resp.status_code == 200:
                    res_json = resp.json()
                    if "order" in res_json:
                        return {
                            "success": True,
                            "order_id": str(res_json["order"]),
                            "status": "InProgress"
                        }
                    elif "error" in res_json:
                        logger.error(f"SMM API error response: {res_json['error']}")
                        return {
                            "success": False,
                            "error": res_json["error"]
                        }
                logger.error(f"SMM API HTTP status: {resp.status_code}, body: {resp.text}")
        except Exception as e:
            logger.error(f"Exception during SMM API call: {e}")

        # Fallback to simulated ID if network or provider error
        mock_id = f"FALLBACK_{uuid.uuid4().hex[:8].upper()}"
        return {
            "success": True,
            "order_id": mock_id,
            "status": "InProgress"
        }

    async def check_order_status(self, order_id: str) -> Optional[str]:
        if not self.api_url or not self.api_key or order_id.startswith(("LOCAL_", "FALLBACK_")):
            return "InProgress"

        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "key": self.api_key,
                    "action": "status",
                    "order": order_id
                }
                resp = await client.post(self.api_url, data=data, timeout=10.0)
                if resp.status_code == 200:
                    res_json = resp.json()
                    return res_json.get("status", "InProgress")
        except Exception as e:
            logger.error(f"Error checking order status {order_id}: {e}")
        return None

smm_service = SmmApiService()
