import uuid
import httpx
from typing import Optional, Dict, Any
from loguru import logger
from bot.config import settings
from bot.services.mock_provider import mock_provider

class SmmProviderClient:
    """
    Asynchronous SMM Provider Client (v2 API standard).
    Supported Services:
    - 👁 Ko'rishlar (Views): standard order
    - ❤️ Reaksiyalar (Reactions): with custom emoji selection (reaction param)
    - 🗳 Ovozlar (Poll Votes): with poll option / answer_number param
    - 🚀 Kanal Boostlari (Telegram Boosts)
    - 👤 Obunachilar (Followers/Members)
    """
    def __init__(self):
        self.api_url = settings.SMM_API_URL
        self.api_key = settings.SMM_API_KEY
        self.proxy = settings.PROXY_URL or None

    def is_configured(self) -> bool:
        return bool(self.api_url and self.api_key and "smm-provider.com" not in self.api_url)

    async def add_order(
        self,
        service_id: int,
        link: str,
        quantity: int,
        service_name: Optional[str] = None,
        reaction: Optional[str] = None,
        answer_number: Optional[str] = None,
        **extra_params
    ) -> Dict[str, Any]:
        """
        Creates an order on the external SMM provider v2 API.
        If provider is not configured or fails, smoothly delegates to MockProvider.
        """
        if not self.is_configured():
            logger.info(f"[SmmProvider] Using mock simulator for service {service_id}, link={link}, qty={quantity}, reaction={reaction}, answer={answer_number}")
            res = await mock_provider.create_demo_order(
                service_id=service_id,
                service_name=service_name or f"Service {service_id}",
                link=link,
                quantity=quantity
            )
            res["reaction"] = reaction
            res["answer_number"] = answer_number
            return res

        payload: Dict[str, Any] = {
            "key": self.api_key,
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity
        }

        # Extra params for Reactions & Poll votes
        if reaction:
            payload["reaction"] = reaction
            payload["reactions"] = reaction
        if answer_number:
            payload["answer_number"] = answer_number
            payload["poll_option"] = answer_number

        for k, v in extra_params.items():
            if v is not None:
                payload[k] = v

        try:
            async with httpx.AsyncClient(proxy=self.proxy, timeout=15.0) as client:
                resp = await client.post(self.api_url, data=payload)
                if resp.status_code == 200:
                    res_json = resp.json()
                    if "order" in res_json:
                        logger.info(f"[SmmProvider] Successfully placed external order: {res_json['order']}")
                        return {
                            "success": True,
                            "order_id": str(res_json["order"]),
                            "status": "InProgress",
                            "is_demo": False
                        }
                    elif "error" in res_json:
                        logger.error(f"[SmmProvider] Provider returned error: {res_json['error']}")
                        return {
                            "success": False,
                            "error": res_json["error"]
                        }
                logger.error(f"[SmmProvider] HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"[SmmProvider] Network exception while adding order: {e}")

        # Fallback to local simulated order if external network fails
        fallback_id = f"LOCAL_FALLBACK_{uuid.uuid4().hex[:8].upper()}"
        logger.warning(f"[SmmProvider] Falling back to local simulated ID {fallback_id}")
        return {
            "success": True,
            "order_id": fallback_id,
            "status": "InProgress",
            "is_demo": True,
            "message": "Buyurtma lokal qabul qilindi (Fallback rejim)."
        }

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Retrieves status of an order from external provider or local mock provider.
        """
        if not self.is_configured() or order_id.startswith(("DEMO_", "LOCAL_", "FALLBACK_")):
            mock_status = await mock_provider.check_order_status(order_id)
            return {
                "success": True,
                "status": mock_status,
                "charge": "0",
                "remains": "0"
            }

        try:
            async with httpx.AsyncClient(proxy=self.proxy, timeout=10.0) as client:
                data = {
                    "key": self.api_key,
                    "action": "status",
                    "order": order_id
                }
                resp = await client.post(self.api_url, data=data)
                if resp.status_code == 200:
                    res_json = resp.json()
                    if "status" in res_json:
                        return {
                            "success": True,
                            "status": res_json.get("status", "InProgress"),
                            "charge": res_json.get("charge", "0"),
                            "remains": res_json.get("remains", "0")
                        }
                    elif "error" in res_json:
                        return {"success": False, "error": res_json["error"]}
        except Exception as e:
            logger.error(f"[SmmProvider] Error checking status for order {order_id}: {e}")

        return {"success": True, "status": "InProgress"}

    async def get_balance(self) -> Dict[str, Any]:
        """
        Fetches balance from external provider.
        """
        if not self.is_configured():
            return {"success": True, "balance": "100.00", "currency": "USD", "is_mock": True}

        try:
            async with httpx.AsyncClient(proxy=self.proxy, timeout=10.0) as client:
                data = {
                    "key": self.api_key,
                    "action": "balance"
                }
                resp = await client.post(self.api_url, data=data)
                if resp.status_code == 200:
                    res_json = resp.json()
                    if "balance" in res_json:
                        return {
                            "success": True,
                            "balance": res_json.get("balance"),
                            "currency": res_json.get("currency", "USD")
                        }
                    elif "error" in res_json:
                        return {"success": False, "error": res_json["error"]}
        except Exception as e:
            logger.error(f"[SmmProvider] Error checking provider balance: {e}")

        return {"success": False, "error": "Provayderga ulanishda xatolik"}


smm_provider = SmmProviderClient()
