import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Bot
    BOT_TOKEN: str = Field(default="")
    BOT_USERNAME: str = Field(default="TurfaSeenBot")
    ADMIN_IDS_RAW: str = Field(default="", alias="ADMIN_IDS")

    # Supabase
    SUPABASE_URL: str = Field(default="")
    SUPABASE_KEY: str = Field(default="")

    # SMM API
    SMM_API_URL: str = Field(default="")
    SMM_API_KEY: str = Field(default="")

    # Proxy (For PythonAnywhere or restricted networks)
    PROXY_URL: str = Field(default="")

    # Webhook / Server
    PORT: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")
    WEBHOOK_URL: str = Field(default="")
    WEBHOOK_PATH: str = Field(default="/webhook")
    USE_POLLING: bool = Field(default=True)

    # Payment & Support
    PAYMENT_CARD_NUMBER: str = Field(default="5614684605929718")
    PAYMENT_COMMENT: str = Field(default="8048583227")
    REFERRAL_REWARD: int = Field(default=80)
    SUPPORT_ADMIN: str = Field(default="@inqiIob")
    OFFICIAL_CHANNEL: str = Field(default="@TurfaSeen")
    WEBSITE_URL: str = Field(default="https://turfaseen.netlify.app")
    WEBAPP_URL: str = Field(default="")

    @property
    def effective_webapp_url(self) -> str:
        return self.WEBAPP_URL or self.WEBSITE_URL or "https://turfaseen.netlify.app"

    @property
    def admin_ids(self) -> List[int]:
        if not self.ADMIN_IDS_RAW:
            return []
        ids = []
        for item in self.ADMIN_IDS_RAW.split(","):
            item = item.strip()
            if item.isdigit():
                ids.append(int(item))
        return ids


settings = Settings()
