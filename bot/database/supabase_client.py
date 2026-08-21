import os
import httpx
from typing import List, Optional, Dict, Any, Union
from loguru import logger
from bot.config import settings
from bot.database.models import UserModel, ChannelModel, ServiceModel, OrderModel, PaymentModel, ReferralModel

class SupabaseClient:
    def __init__(self):
        self.base_url = settings.SUPABASE_URL.rstrip('/') if settings.SUPABASE_URL else ""
        self.key = settings.SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.proxy = settings.PROXY_URL or os.environ.get("http_proxy") or os.environ.get("https_proxy")
        if not self.proxy and (os.path.exists("/home/Quvonch005") or "pythonanywhere" in os.environ.get("PYTHONANYWHERE_SITE", "").lower() or os.path.exists("/var/www")):
            self.proxy = "http://proxy.server:3128"

        # In-memory mock storage for reliable local sandbox demo testing
        self._mock_users: Dict[int, UserModel] = {}
        self._mock_channels: List[ChannelModel] = [
            ChannelModel(id=1, name="siyasi", link="https://t.me/siyasi_rasmiy", username="@siyasi_rasmiy", is_active=True),
            ChannelModel(id=2, name="Turfa Seen | Rasmiy", link="https://t.me/TurfaSeen", username="@TurfaSeen", is_active=True),
            ChannelModel(id=3, name="— Sukut saqlang!", link="https://t.me/sukut_saqlang", username="@sukut_saqlang", is_active=True),
            ChannelModel(id=4, name="— Manfaati", link="https://t.me/manfaati_uz", username="@manfaati_uz", is_active=True),
        ]
        self._mock_services: List[ServiceModel] = [
            # Telegram - Obunachi
            ServiceModel(id=1, platform="Telegram", category="Obunachi", service_id_external=340, name="Tekin Obunachi", price_per_1000=0, min_order=1, max_order=40, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi! Kuniga 1 marta buyurtma berish mumkin.", estimated_time="1-5 daqiqa (Demo)", is_free=True, is_demo=True),
            ServiceModel(id=2, platform="Telegram", category="Obunachi", service_id_external=101, name="30 Kun kafolat", price_per_1000=8900, min_order=50, max_order=50000, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi!", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=3, platform="Telegram", category="Obunachi", service_id_external=102, name="60 Kun kafolat", price_per_1000=13820, min_order=50, max_order=50000, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi! Tezkor qo'shilish.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=4, platform="Telegram", category="Obunachi", service_id_external=103, name="90 Kun kafolat", price_per_1000=15700, min_order=50, max_order=50000, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi! Sifatli obunachilar.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=5, platform="Telegram", category="Obunachi", service_id_external=104, name="180 Kun kafolat", price_per_1000=19999, min_order=100, max_order=100000, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi! Yuqori sifat.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=6, platform="Telegram", category="Obunachi", service_id_external=105, name="365 Kun kafolat", price_per_1000=35879, min_order=100, max_order=100000, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi! 1 yil kafolat.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            
            # Telegram - Reaksiya (with custom reaction emoji selection)
            ServiceModel(id=33, platform="Telegram", category="Reaksiya", service_id_external=200, name="🎁 Tekin Reaksiya (50 tagacha)", price_per_1000=0, min_order=1, max_order=50, description="Telegram postlari uchun 50 tagacha mutlaqo bepul reaksiya! Istalgan emojini tanlang.", estimated_time="1-3 daqiqa", is_free=True, is_demo=True, requires_reaction=True),
            ServiceModel(id=7, platform="Telegram", category="Reaksiya", service_id_external=201, name="Tanlangan emoji reaksiyasi (👍❤️🔥)", price_per_1000=1200, min_order=10, max_order=100000, description="Emoji tanlash imkoniyati bilan post reaksiyalari.", estimated_time="1-3 daqiqa", is_free=False, is_demo=True, requires_reaction=True),
            ServiceModel(id=8, platform="Telegram", category="Reaksiya", service_id_external=202, name="Ijobiy reaksiyalar (❤️👏🎉)", price_per_1000=1500, min_order=10, max_order=50000, description="Faqat ijobiy emojilar (Love, Clap, Party).", estimated_time="1-3 daqiqa", is_free=False, is_demo=True, requires_reaction=False),
            ServiceModel(id=27, platform="Telegram", category="Reaksiya", service_id_external=203, name="Maxsus tezkor reaksiyalar (⚡🤩)", price_per_1000=1800, min_order=10, max_order=50000, description="Tezkor yetkazib beriluvchi reaksiyalar.", estimated_time="1-2 daqiqa", is_free=False, is_demo=True, requires_reaction=True),

            # Telegram - Ko'rishlar (Views)
            ServiceModel(id=9, platform="Telegram", category="Ko'rishlar", service_id_external=301, name="Oxirgi 1 ta post ko'rishlar", price_per_1000=350, min_order=50, max_order=500000, description="Post havolasini yuboring.", estimated_time="1 daqiqa", is_free=False, is_demo=True),
            ServiceModel(id=10, platform="Telegram", category="Ko'rishlar", service_id_external=302, name="Oxirgi 5 ta post ko'rishlar", price_per_1000=1400, min_order=50, max_order=100000, description="Kanal havolasini yuboring.", estimated_time="2-5 daqiqa", is_free=False, is_demo=True),
            ServiceModel(id=11, platform="Telegram", category="Ko'rishlar", service_id_external=303, name="Oxirgi 10 ta post ko'rishlar", price_per_1000=2500, min_order=50, max_order=100000, description="Kanal havolasini yuboring.", estimated_time="3-10 daqiqa", is_free=False, is_demo=True),
            ServiceModel(id=28, platform="Telegram", category="Ko'rishlar", service_id_external=304, name="Avto-ko'rishlar (Tezkor)", price_per_1000=500, min_order=100, max_order=500000, description="Tezkor yetkaziluvchi ko'rishlar.", estimated_time="1 daqiqa", is_free=False, is_demo=True),

            # Telegram - Ovozlar (Poll Votes)
            ServiceModel(id=29, platform="Telegram", category="Ovozlar", service_id_external=450, name="So'rovnoma ovozlari (Variant tanlash)", price_per_1000=12000, min_order=10, max_order=50000, description="So'rovnoma posti havolasi va variant raqami tanlanadi.", estimated_time="2-5 daqiqa", is_free=False, is_demo=True, requires_poll_option=True),
            ServiceModel(id=30, platform="Telegram", category="Ovozlar", service_id_external=451, name="Anonim so'rovnoma ovozi", price_per_1000=15000, min_order=10, max_order=30000, description="Anonim so'rovnomalar uchun xavfsiz ovozlar.", estimated_time="2-5 daqiqa", is_free=False, is_demo=True, requires_poll_option=True),

            # Telegram - Boostlar / Boost ovoz (Telegram Boosts)
            ServiceModel(id=12, platform="Telegram", category="Boost ovoz", service_id_external=401, name="Kanal uchun Boost (1 kunlik)", price_per_1000=4500, min_order=1, max_order=500, description="Kanal havolasini yuboring. 1 kunlik daraja oshirish.", estimated_time="1-5 daqiqa", is_free=False, is_demo=True),
            ServiceModel(id=13, platform="Telegram", category="Boost ovoz", service_id_external=402, name="Kanal uchun Boost (7 kunlik)", price_per_1000=18000, min_order=1, max_order=500, description="Kanal havolasini yuboring. 7 kunlik daraja oshirish.", estimated_time="1-5 daqiqa", is_free=False, is_demo=True),
            ServiceModel(id=31, platform="Telegram", category="Boost ovoz", service_id_external=403, name="Kanal uchun Boost (30 kunlik)", price_per_1000=55000, min_order=1, max_order=500, description="Kanal havolasini yuboring. 30 kunlik daraja oshirish.", estimated_time="1-5 daqiqa", is_free=False, is_demo=True),
            ServiceModel(id=32, platform="Telegram", category="Boost ovoz", service_id_external=404, name="Guruh uchun Boost (7 kunlik)", price_per_1000=22000, min_order=1, max_order=500, description="Guruh havolasini yuboring.", estimated_time="1-5 daqiqa", is_free=False, is_demo=True),

            # Telegram - Hikoya & O'zbek tarmoq
            ServiceModel(id=14, platform="Telegram", category="Hikoya", service_id_external=501, name="Telegram Story ko'rishlar", price_per_1000=2900, min_order=50, max_order=50000, description="Foydalanuvchi yoki kanal story havolasini yuboring.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=15, platform="Telegram", category="O'zbek tarmoq", service_id_external=601, name="O'zbek jonli obunachi", price_per_1000=28000, min_order=50, max_order=20000, description="Faqat ommaviy o'zbek kanallari uchun.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=16, platform="Telegram", category="O'zbek tarmoq", service_id_external=602, name="O'zbek post ko'rishlar", price_per_1000=800, min_order=100, max_order=50000, description="O'zbek auditoriyasi ko'rishlari.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),

            # Instagram
            ServiceModel(id=17, platform="Instagram", category="Obunachi", service_id_external=701, name="Instagram Kafolatsiz Obunachi", price_per_1000=7500, min_order=50, max_order=100000, description="Profil ochiq (public) bo'lishi shart.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=18, platform="Instagram", category="Obunachi", service_id_external=702, name="Instagram 30 Kun Kafolatli", price_per_1000=14500, min_order=50, max_order=100000, description="Profil ochiq bo'lishi shart.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=19, platform="Instagram", category="Ko'rishlar", service_id_external=703, name="Instagram Reels ko'rishlar", price_per_1000=400, min_order=100, max_order=1000000, description="Reels video havolasi kerak.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=20, platform="Instagram", category="Reaksiya", service_id_external=704, name="Instagram Post Layklari", price_per_1000=3500, min_order=50, max_order=50000, description="Post havolasi kerak.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),

            # YouTube
            ServiceModel(id=21, platform="YouTube", category="Obunachi", service_id_external=801, name="YouTube Obunachi (Real)", price_per_1000=85000, min_order=50, max_order=10000, description="Kanal havolasini yuboring.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=22, platform="YouTube", category="Ko'rishlar", service_id_external=802, name="YouTube Video Ko'rishlar", price_per_1000=19000, min_order=100, max_order=500000, description="Video havolasini yuboring.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=23, platform="YouTube", category="Reaksiya", service_id_external=803, name="YouTube Like", price_per_1000=12000, min_order=50, max_order=20000, description="Video havolasini yuboring.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),

            # TikTok
            ServiceModel(id=24, platform="TikTok", category="Obunachi", service_id_external=901, name="TikTok Obunachi", price_per_1000=18000, min_order=50, max_order=50000, description="TikTok profil havolasi kerak.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=25, platform="TikTok", category="Ko'rishlar", service_id_external=902, name="TikTok Video Ko'rishlar", price_per_1000=250, min_order=100, max_order=1000000, description="Video havolasini yuboring.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
            ServiceModel(id=26, platform="TikTok", category="Reaksiya", service_id_external=903, name="TikTok Layklar", price_per_1000=6500, min_order=50, max_order=50000, description="Video havolasini yuboring.", estimated_time="1-5 daqiqa (Demo)", is_free=False, is_demo=True),
        ]
        self._mock_orders: List[OrderModel] = []
        self._mock_payments: List[PaymentModel] = []
        self._mock_referrals: List[ReferralModel] = []

    def _is_configured(self) -> bool:
        return bool(self.base_url and self.key and "your-project" not in self.base_url and "medkoavebevxbmurgyol" not in self.base_url)

    async def get_user(self, telegram_id: int) -> Optional[UserModel]:
        if not self._is_configured():
            return self._mock_users.get(telegram_id)
        
        try:
            async with httpx.AsyncClient(proxy=self.proxy) as client:
                resp = await client.get(
                    f"{self.base_url}/rest/v1/users?telegram_id=eq.{telegram_id}&select=*",
                    headers=self.headers,
                    timeout=5.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        return UserModel(**data[0])
        except Exception as e:
            logger.error(f"Error getting user {telegram_id}: {e}")
        return self._mock_users.get(telegram_id)

    async def create_or_get_user(
        self, 
        telegram_id: int, 
        username: Optional[str] = None, 
        first_name: Optional[str] = None,
        referrer_id: Optional[int] = None
    ) -> tuple[UserModel, bool]:
        existing = await self.get_user(telegram_id)
        if existing:
            if existing.username != username or existing.first_name != first_name:
                await self.update_user_profile(telegram_id, username, first_name)
            return existing, False

        new_user = UserModel(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            balance=50000,  # 50 000 demo UZS initial sandbox balance
            total_deposit=0,
            referral_id=referrer_id if (referrer_id and referrer_id != telegram_id) else None,
            referral_count=0,
            is_banned=False,
            is_demo=True
        )

        if not self._is_configured():
            self._mock_users[telegram_id] = new_user
            return new_user, True

        try:
            async with httpx.AsyncClient(proxy=self.proxy) as client:
                payload = new_user.model_dump(exclude={"id", "created_at"}, exclude_none=True)
                resp = await client.post(
                    f"{self.base_url}/rest/v1/users",
                    headers=self.headers,
                    json=payload,
                    timeout=5.0
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    if data:
                        return UserModel(**data[0]), True
        except Exception as e:
            logger.error(f"Error creating user {telegram_id}: {e}")

        self._mock_users[telegram_id] = new_user
        return new_user, True

    async def update_user_profile(self, telegram_id: int, username: Optional[str], first_name: Optional[str]) -> bool:
        if not self._is_configured():
            user = self._mock_users.get(telegram_id)
            if user:
                user.username = username
                user.first_name = first_name
                return True
            return False

        try:
            async with httpx.AsyncClient(proxy=self.proxy) as client:
                resp = await client.patch(
                    f"{self.base_url}/rest/v1/users?telegram_id=eq.{telegram_id}",
                    headers=self.headers,
                    json={"username": username, "first_name": first_name},
                    timeout=5.0
                )
                return resp.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Error updating profile {telegram_id}: {e}")
            return False

    async def update_balance(self, telegram_id: int, amount: int, is_deposit: bool = False) -> bool:
        user = await self.get_user(telegram_id)
        if not user:
            return False

        new_balance = max(0, user.balance + amount)
        new_deposit = user.total_deposit + (amount if is_deposit and amount > 0 else 0)

        if not self._is_configured():
            user.balance = new_balance
            user.total_deposit = new_deposit
            self._mock_users[telegram_id] = user
            return True

        try:
            async with httpx.AsyncClient(proxy=self.proxy) as client:
                payload = {"balance": new_balance}
                if is_deposit and amount > 0:
                    payload["total_deposit"] = new_deposit
                resp = await client.patch(
                    f"{self.base_url}/rest/v1/users?telegram_id=eq.{telegram_id}",
                    headers=self.headers,
                    json=payload,
                    timeout=5.0
                )
                if resp.status_code in (200, 204):
                    user.balance = new_balance
                    return True
        except Exception as e:
            logger.error(f"Error updating balance {telegram_id}: {e}")
            user.balance = new_balance
            self._mock_users[telegram_id] = user
            return True
        return False

    async def add_referral_reward(self, referrer_id: int, referred_id: int, reward: int = 80) -> bool:
        if referrer_id == referred_id:
            return False

        referrer = await self.get_user(referrer_id)
        if not referrer:
            return False

        await self.update_balance(referrer_id, reward, is_deposit=False)
        referrer.referral_count += 1
        self._mock_referrals.append(ReferralModel(referrer_id=referrer_id, referred_id=referred_id, reward=reward, is_demo=True))
        return True

    async def get_active_channels(self) -> List[ChannelModel]:
        return self._mock_channels

    async def get_categories_by_platform(self, platform: str) -> List[str]:
        services = [s for s in self._mock_services if s.platform.lower() == platform.lower()]
        cats = []
        for s in services:
            if s.category not in cats:
                cats.append(s.category)
        return cats or ["Obunachi", "Ko'rishlar", "Reaksiya"]

    async def get_services_by_category(self, platform: str, category: str) -> List[ServiceModel]:
        return [
            s for s in self._mock_services 
            if s.platform.lower() == platform.lower() and s.category.lower() == category.lower()
        ]

    async def get_service_by_id(self, service_id: int) -> Optional[ServiceModel]:
        for s in self._mock_services:
            if s.id == service_id:
                return s
        return None

    async def create_order(
        self,
        user_telegram_id: Optional[int] = None,
        service_id: Optional[int] = None,
        service_name: Optional[str] = None,
        link: Optional[str] = None,
        quantity: Optional[int] = None,
        price: Optional[int] = None,
        status: str = "demo_processing",
        external_order_id: Optional[str] = None,
        estimated_time: str = "1-5 daqiqa (Demo)",
        order: Optional[OrderModel] = None
    ) -> OrderModel:
        if order is None:
            order = OrderModel(
                id=len(self._mock_orders) + 1,
                user_telegram_id=user_telegram_id or 0,
                service_id=service_id,
                service_name=service_name,
                link=link or "",
                quantity=quantity or 0,
                price=price or 0,
                status=status,
                estimated_time=estimated_time,
                is_demo=True,
                external_order_id=external_order_id
            )
        else:
            if not order.id:
                order.id = len(self._mock_orders) + 1
            order.is_demo = True

        self._mock_orders.append(order)
        return order

    async def update_order_status(self, order_id: int, status: str) -> Optional[OrderModel]:
        for ord_item in self._mock_orders:
            if ord_item.id == order_id:
                ord_item.status = status
                return ord_item
        return None

    async def get_user_orders(self, telegram_id: int, limit: int = 10) -> List[OrderModel]:
        user_orders = [o for o in self._mock_orders if o.user_telegram_id == telegram_id]
        return list(reversed(user_orders))[:limit]

    async def create_payment(self, payment: PaymentModel) -> Optional[PaymentModel]:
        payment.id = len(self._mock_payments) + 1
        payment.is_demo = True
        self._mock_payments.append(payment)
        return payment

    async def get_payment_by_id(self, payment_id: int) -> Optional[PaymentModel]:
        for p in self._mock_payments:
            if p.id == payment_id:
                return p
        return None

    async def update_payment_status(self, payment_id: int, status: str, amount: Optional[int] = None) -> bool:
        for p in self._mock_payments:
            if p.id == payment_id:
                p.status = status
                if amount is not None:
                    p.amount = amount
                return True
        return False

    async def get_top_referrers(self, limit: int = 10) -> List[UserModel]:
        users = list(self._mock_users.values())
        users.sort(key=lambda u: u.referral_count, reverse=True)
        return users[:limit]

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_users": len(self._mock_users),
            "total_orders": len(self._mock_orders),
            "pending_payments": len([p for p in self._mock_payments if p.status in ("Pending", "demo_pending")]),
            "completed_orders": len([o for o in self._mock_orders if o.status == "demo_completed"]),
            "is_demo_mode": True
        }

    async def get_admin_stats(self) -> Dict[str, Any]:
        return await self.get_statistics()


db = SupabaseClient()
