import json
import os
from typing import Dict, Any, Optional
from loguru import logger
from bot.config import settings

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "bot_settings.json")

DEFAULT_WELCOME_MESSAGE = (
    "Assalomu alaykum, <b>{first_name}</b>!\n\n"
    "🚀 <b>Turfa Seen</b> platformasiga xush kelibsiz!\n"
    "Quyidagi <b>'🚀 Ilovani ochish'</b> tugmasi orqali qulay va zamonaviy Mini App interfeysidan foydalanishingiz yoki bot menyusidan xizmatlarga buyurtma berishingiz mumkin."
)

class SettingsService:
    def __init__(self):
        self._data: Dict[str, Any] = {
            "payment_card_number": settings.PAYMENT_CARD_NUMBER or "5614684605929718",
            "payment_comment": settings.PAYMENT_COMMENT or "8048583227",
            "welcome_message": DEFAULT_WELCOME_MESSAGE,
            "support_admin": settings.SUPPORT_ADMIN or "@inqiIob",
            "official_channel": settings.OFFICIAL_CHANNEL or "@TurfaSeen",
            "website_url": settings.WEBSITE_URL or "https://turfaseen.netlify.app",
            "referral_reward": settings.REFERRAL_REWARD or 80,
            "smm_api_url": settings.SMM_API_URL or "",
            "smm_api_key": settings.SMM_API_KEY or ""
        }
        self.load_settings()

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        self._data.update(saved)
                        logger.info("Bot dynamic settings loaded successfully from bot_settings.json")
        except Exception as e:
            logger.error(f"Error loading bot_settings.json: {e}")

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
                logger.info("Bot dynamic settings saved to bot_settings.json")
        except Exception as e:
            logger.error(f"Error saving bot_settings.json: {e}")

    def get_card_number(self) -> str:
        return self._data.get("payment_card_number", settings.PAYMENT_CARD_NUMBER)

    def set_card_number(self, card_number: str):
        self._data["payment_card_number"] = card_number.strip()
        self.save_settings()

    def get_card_comment(self) -> str:
        return self._data.get("payment_comment", settings.PAYMENT_COMMENT)

    def set_card_comment(self, comment: str):
        self._data["payment_comment"] = comment.strip()
        self.save_settings()

    def get_welcome_message(self, first_name: str = "Foydalanuvchi") -> str:
        raw = self._data.get("welcome_message") or DEFAULT_WELCOME_MESSAGE
        return raw.replace("{first_name}", first_name or "Foydalanuvchi")

    def get_raw_welcome_message(self) -> str:
        return self._data.get("welcome_message") or DEFAULT_WELCOME_MESSAGE

    def set_welcome_message(self, message_text: str):
        self._data["welcome_message"] = message_text.strip()
        self.save_settings()

    def reset_welcome_message(self):
        self._data["welcome_message"] = DEFAULT_WELCOME_MESSAGE
        self.save_settings()

    def get_support_admin(self) -> str:
        return self._data.get("support_admin", settings.SUPPORT_ADMIN)

    def set_support_admin(self, admin_username: str):
        self._data["support_admin"] = admin_username.strip()
        self.save_settings()

    def get_smm_api_url(self) -> str:
        return self._data.get("smm_api_url") or settings.SMM_API_URL or ""

    def set_smm_api_url(self, url: str):
        self._data["smm_api_url"] = url.strip()
        self.save_settings()

    def get_smm_api_key(self) -> str:
        return self._data.get("smm_api_key") or settings.SMM_API_KEY or ""

    def set_smm_api_key(self, key: str):
        self._data["smm_api_key"] = key.strip()
        self.save_settings()

    def is_real_smm_configured(self) -> bool:
        url = self.get_smm_api_url()
        key = self.get_smm_api_key()
        return bool(url and key and "smm-provider.com" not in url and key != "your_smm_api_key")

settings_service = SettingsService()

