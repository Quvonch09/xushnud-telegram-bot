import hmac
import hashlib
import json
import urllib.parse
from typing import Optional, Dict, Any
from bot.config import settings

def validate_telegram_init_data(init_data: str, bot_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Validates Telegram WebApp initData string using HMAC-SHA256 signature verification.
    
    Returns parsed data dictionary if valid, otherwise None.
    """
    token = bot_token or settings.BOT_TOKEN
    if not init_data or not token or token == "MOCK_TOKEN":
        return None

    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            return None

        # Sort keys alphabetically and join as key=value separated by \n
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = "\n".join(data_check_arr)

        # Secret key = HMAC-SHA256("WebAppData", bot_token)
        secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()

        # Calculated hash = HMAC-SHA256(secret_key, data_check_string)
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if hmac.compare_digest(calculated_hash, received_hash):
            # Parse user JSON if present
            if "user" in parsed_data:
                try:
                    parsed_data["user"] = json.loads(parsed_data["user"])
                except Exception:
                    pass
            return parsed_data
        return None
    except Exception:
        return None
