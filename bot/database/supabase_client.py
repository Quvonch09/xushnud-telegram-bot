import httpx
from typing import List, Optional, Dict, Any
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
        # In-memory mock storage fallback for local development without active Supabase credentials
        self._mock_users: Dict[int, UserModel] = {}
        self._mock_channels: List[ChannelModel] = [
            ChannelModel(id=1, name="siyasi", link="https://t.me/siyasi_rasmiy", username="@siyasi_rasmiy", is_active=True),
            ChannelModel(id=2, name="Turfa Seen | Rasmiy", link="https://t.me/TurfaSeen", username="@TurfaSeen", is_active=True),
            ChannelModel(id=3, name="— Sukut saqlang!", link="https://t.me/sukut_saqlang", username="@sukut_saqlang", is_active=True),
            ChannelModel(id=4, name="— Manfaati", link="https://t.me/manfaati_uz", username="@manfaati_uz", is_active=True),
        ]
        self._mock_services: List[ServiceModel] = [
            # Telegram
            ServiceModel(id=1, platform="Telegram", category="Obunachi", service_id_external=340, name="Tekin Obunachi", price_per_1000=0, min_order=1, max_order=40, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi! Kuniga 1 marta buyurtma berish mumkin.", is_free=True),
            ServiceModel(id=2, platform="Telegram", category="Obunachi", service_id_external=101, name="30 Kun kafolat", price_per_1000=8900, min_order=50, max_order=50000, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi!", is_free=False),
            ServiceModel(id=3, platform="Telegram", category="Obunachi", service_id_external=102, name="60 Kun kafolat", price_per_1000=13820, min_order=50, max_order=50000, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi! Tezkor qo'shilish.", is_free=False),
            ServiceModel(id=4, platform="Telegram", category="Obunachi", service_id_external=103, name="90 Kun kafolat", price_per_1000=15700, min_order=50, max_order=50000, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi! Sifatli obunachilar.", is_free=False),
            ServiceModel(id=5, platform="Telegram", category="Obunachi", service_id_external=104, name="180 Kun kafolat", price_per_1000=19999, min_order=100, max_order=100000, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi! Yuqori sifat.", is_free=False),
            ServiceModel(id=6, platform="Telegram", category="Obunachi", service_id_external=105, name="365 Kun kafolat", price_per_1000=35879, min_order=100, max_order=100000, description="Faqat ommaviy kanal va guruhlar uchun ishlaydi! 1 yil kafolat.", is_free=False),
            ServiceModel(id=7, platform="Telegram", category="Reaksiya", service_id_external=201, name="Aralash reaksiyalar (👍❤️🔥)", price_per_1000=1200, min_order=10, max_order=100000, description="Post havolasini yuboring. Tezkor ishga tushish.", is_free=False),
            ServiceModel(id=8, platform="Telegram", category="Reaksiya", service_id_external=202, name="Ijobiy reaksiyalar (❤️👏🎉)", price_per_1000=1500, min_order=10, max_order=50000, description="Post havolasini yuboring.", is_free=False),
            ServiceModel(id=9, platform="Telegram", category="Ko'rishlar", service_id_external=301, name="Oxirgi 1 ta post ko'rishlar", price_per_1000=350, min_order=50, max_order=500000, description="Post havolasini yuboring.", is_free=False),
            ServiceModel(id=10, platform="Telegram", category="Ko'rishlar", service_id_external=302, name="Oxirgi 5 ta post ko'rishlar", price_per_1000=1400, min_order=50, max_order=100000, description="Kanal havolasini yuboring.", is_free=False),
            ServiceModel(id=11, platform="Telegram", category="Ko'rishlar", service_id_external=303, name="Oxirgi 10 ta post ko'rishlar", price_per_1000=2500, min_order=50, max_order=100000, description="Kanal havolasini yuboring.", is_free=False),
            ServiceModel(id=12, platform="Telegram", category="Boost ovoz", service_id_external=401, name="Kanal uchun Boost (1 kunlik)", price_per_1000=4500, min_order=1, max_order=500, description="Kanal havolasini yuboring.", is_free=False),
            ServiceModel(id=13, platform="Telegram", category="Boost ovoz", service_id_external=402, name="Kanal uchun Boost (7 kunlik)", price_per_1000=18000, min_order=1, max_order=500, description="Kanal havolasini yuboring.", is_free=False),
            ServiceModel(id=14, platform="Telegram", category="Hikoya", service_id_external=501, name="Telegram Story ko'rishlar", price_per_1000=2900, min_order=50, max_order=50000, description="Foydalanuvchi yoki kanal story havolasini yuboring.", is_free=False),
            ServiceModel(id=15, platform="Telegram", category="O'zbek tarmoq", service_id_external=601, name="O'zbek jonli obunachi", price_per_1000=28000, min_order=50, max_order=20000, description="Faqat ommaviy o'zbek kanallari uchun.", is_free=False),
            ServiceModel(id=16, platform="Telegram", category="O'zbek tarmoq", service_id_external=602, name="O'zbek post ko'rishlar", price_per_1000=800, min_order=100, max_order=50000, description="O'zbek auditoriyasi ko'rishlari.", is_free=False),
            # Instagram
            ServiceModel(id=17, platform="Instagram", category="Obunachi", service_id_external=701, name="Instagram Kafolatsiz Obunachi", price_per_1000=7500, min_order=50, max_order=100000, description="Profil ochiq (public) bo'lishi shart.", is_free=False),
            ServiceModel(id=18, platform="Instagram", category="Obunachi", service_id_external=702, name="Instagram 30 Kun Kafolatli", price_per_1000=14500, min_order=50, max_order=100000, description="Profil ochiq bo'lishi shart.", is_free=False),
            ServiceModel(id=19, platform="Instagram", category="Ko'rishlar", service_id_external=703, name="Instagram Reels ko'rishlar", price_per_1000=400, min_order=100, max_order=1000000, description="Reels video havolasi kerak.", is_free=False),
            ServiceModel(id=20, platform="Instagram", category="Reaksiya", service_id_external=704, name="Instagram Post Layklari", price_per_1000=3500, min_order=50, max_order=50000, description="Post havolasi kerak.", is_free=False),
            # YouTube
            ServiceModel(id=21, platform="YouTube", category="Obunachi", service_id_external=801, name="YouTube Obunachi (Real)", price_per_1000=85000, min_order=50, max_order=10000, description="Kanal havolasini yuboring.", is_free=False),
            ServiceModel(id=22, platform="YouTube", category="Ko'rishlar", service_id_external=802, name="YouTube Video Ko'rishlar", price_per_1000=19000, min_order=100, max_order=500000, description="Video havolasini yuboring.", is_free=False),
            ServiceModel(id=23, platform="YouTube", category="Reaksiya", service_id_external=803, name="YouTube Like", price_per_1000=12000, min_order=50, max_order=20000, description="Video havolasini yuboring.", is_free=False),
            # TikTok
            ServiceModel(id=24, platform="TikTok", category="Obunachi", service_id_external=901, name="TikTok Obunachi", price_per_1000=18000, min_order=50, max_order=50000, description="TikTok profil havolasi kerak.", is_free=False),
            ServiceModel(id=25, platform="TikTok", category="Ko'rishlar", service_id_external=902, name="TikTok Video Ko'rishlar", price_per_1000=250, min_order=100, max_order=1000000, description="Video havolasini yuboring.", is_free=False),
            ServiceModel(id=26, platform="TikTok", category="Reaksiya", service_id_external=903, name="TikTok Layklar", price_per_1000=6500, min_order=50, max_order=50000, description="Video havolasini yuboring.", is_free=False),
        ]
        self._mock_orders: List[OrderModel] = []
        self._mock_payments: List[PaymentModel] = []
        self._mock_referrals: List[ReferralModel] = []

    def _is_configured(self) -> bool:
        return bool(self.base_url and self.key and "your-project" not in self.base_url)

    async def get_user(self, telegram_id: int) -> Optional[UserModel]:
        if not self._is_configured():
            return self._mock_users.get(telegram_id)
        
        try:
            async with httpx.AsyncClient() as client:
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
        return None

    async def create_or_get_user(
        self, 
        telegram_id: int, 
        username: Optional[str] = None, 
        first_name: Optional[str] = None,
        referrer_id: Optional[int] = None
    ) -> tuple[UserModel, bool]:
        """
        Returns (user, is_new)
        """
        existing = await self.get_user(telegram_id)
        if existing:
            # Update username / first_name if changed
            if existing.username != username or existing.first_name != first_name:
                await self.update_user_profile(telegram_id, username, first_name)
            return existing, False

        # Create new user
        new_user = UserModel(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            balance=0,
            total_deposit=0,
            referral_id=referrer_id if (referrer_id and referrer_id != telegram_id) else None,
            referral_count=0,
            is_banned=False
        )

        if not self._is_configured():
            self._mock_users[telegram_id] = new_user
            return new_user, True

        try:
            async with httpx.AsyncClient() as client:
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

    async def update_user_profile(self, telegram_id: int, username: Optional[str], first_name: Optional[str]):
        if not self._is_configured():
            if telegram_id in self._mock_users:
                self._mock_users[telegram_id].username = username
                self._mock_users[telegram_id].first_name = first_name
            return

        try:
            async with httpx.AsyncClient() as client:
                await client.patch(
                    f"{self.base_url}/rest/v1/users?telegram_id=eq.{telegram_id}",
                    headers=self.headers,
                    json={"username": username, "first_name": first_name},
                    timeout=5.0
                )
        except Exception as e:
            logger.error(f"Error updating user profile {telegram_id}: {e}")

    async def add_referral_reward(self, referrer_id: int, referred_id: int, reward: int = 80) -> bool:
        """
        Awards referrer balance & increments referral count
        """
        referrer = await self.get_user(referrer_id)
        if not referrer:
            return False

        new_balance = referrer.balance + reward
        new_ref_count = referrer.referral_count + 1

        if not self._is_configured():
            referrer.balance = new_balance
            referrer.referral_count = new_ref_count
            self._mock_referrals.append(ReferralModel(
                referrer_id=referrer_id,
                referred_id=referred_id,
                reward=reward
            ))
            return True

        try:
            async with httpx.AsyncClient() as client:
                # Update user
                await client.patch(
                    f"{self.base_url}/rest/v1/users?telegram_id=eq.{referrer_id}",
                    headers=self.headers,
                    json={"balance": new_balance, "referral_count": new_ref_count},
                    timeout=5.0
                )
                # Log referral
                await client.post(
                    f"{self.base_url}/rest/v1/referrals",
                    headers=self.headers,
                    json={"referrer_id": referrer_id, "referred_id": referred_id, "reward": reward},
                    timeout=5.0
                )
                return True
        except Exception as e:
            logger.error(f"Error rewarding referral {referrer_id}: {e}")
            return False

    async def update_balance(self, telegram_id: int, amount: int, is_deposit: bool = False) -> bool:
        user = await self.get_user(telegram_id)
        if not user:
            return False

        new_balance = user.balance + amount
        new_total_deposit = user.total_deposit + (amount if is_deposit and amount > 0 else 0)

        if not self._is_configured():
            user.balance = new_balance
            user.total_deposit = new_total_deposit
            return True

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{self.base_url}/rest/v1/users?telegram_id=eq.{telegram_id}",
                    headers=self.headers,
                    json={"balance": new_balance, "total_deposit": new_total_deposit},
                    timeout=5.0
                )
                return resp.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Error updating balance {telegram_id}: {e}")
            return False

    async def get_active_channels(self) -> List[ChannelModel]:
        if not self._is_configured():
            return [c for c in self._mock_channels if c.is_active]

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/rest/v1/channels?is_active=eq.true&select=*",
                    headers=self.headers,
                    timeout=5.0
                )
                if resp.status_code == 200:
                    return [ChannelModel(**item) for item in resp.json()]
        except Exception as e:
            logger.error(f"Error getting channels: {e}")
        return [c for c in self._mock_channels if c.is_active]

    async def get_platforms(self) -> List[str]:
        services = await self.get_services()
        platforms = []
        for s in services:
            if s.platform not in platforms:
                platforms.append(s.platform)
        return platforms or ["Telegram", "Instagram", "YouTube", "TikTok"]

    async def get_categories_by_platform(self, platform: str) -> List[str]:
        services = await self.get_services(platform=platform)
        cats = []
        for s in services:
            if s.category not in cats:
                cats.append(s.category)
        return cats

    async def get_services(self, platform: Optional[str] = None, category: Optional[str] = None) -> List[ServiceModel]:
        if not self._is_configured():
            res = self._mock_services
            if platform:
                res = [s for s in res if s.platform.lower() == platform.lower()]
            if category:
                res = [s for s in res if s.category.lower() == category.lower()]
            return res

        try:
            query = f"{self.base_url}/rest/v1/services?select=*"
            if platform:
                query += f"&platform=eq.{platform}"
            if category:
                query += f"&category=eq.{category}"
            query += "&order=id.asc"

            async with httpx.AsyncClient() as client:
                resp = await client.get(query, headers=self.headers, timeout=5.0)
                if resp.status_code == 200:
                    return [ServiceModel(**item) for item in resp.json()]
        except Exception as e:
            logger.error(f"Error getting services: {e}")
        
        # Fallback
        res = self._mock_services
        if platform:
            res = [s for s in res if s.platform.lower() == platform.lower()]
        if category:
            res = [s for s in res if s.category.lower() == category.lower()]
        return res

    async def get_service_by_id(self, service_id: int) -> Optional[ServiceModel]:
        if not self._is_configured():
            for s in self._mock_services:
                if s.id == service_id:
                    return s
            return None

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/rest/v1/services?id=eq.{service_id}&select=*",
                    headers=self.headers,
                    timeout=5.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        return ServiceModel(**data[0])
        except Exception as e:
            logger.error(f"Error getting service {service_id}: {e}")
        
        for s in self._mock_services:
            if s.id == service_id:
                return s
        return None

    async def create_order(self, order: OrderModel) -> Optional[OrderModel]:
        if not self._is_configured():
            order.id = len(self._mock_orders) + 1
            self._mock_orders.append(order)
            return order

        try:
            async with httpx.AsyncClient() as client:
                payload = order.model_dump(exclude={"id", "created_at"}, exclude_none=True)
                resp = await client.post(
                    f"{self.base_url}/rest/v1/orders",
                    headers=self.headers,
                    json=payload,
                    timeout=5.0
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    if data:
                        return OrderModel(**data[0])
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            order.id = len(self._mock_orders) + 1
            self._mock_orders.append(order)
            return order
        return None

    async def get_user_orders(self, telegram_id: int, limit: int = 10) -> List[OrderModel]:
        if not self._is_configured():
            user_orders = [o for o in self._mock_orders if o.user_telegram_id == telegram_id]
            return list(reversed(user_orders))[:limit]

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/rest/v1/orders?user_telegram_id=eq.{telegram_id}&order=id.desc&limit={limit}&select=*",
                    headers=self.headers,
                    timeout=5.0
                )
                if resp.status_code == 200:
                    return [OrderModel(**item) for item in resp.json()]
        except Exception as e:
            logger.error(f"Error getting user orders: {e}")
        return []

    async def create_payment(self, payment: PaymentModel) -> Optional[PaymentModel]:
        if not self._is_configured():
            payment.id = len(self._mock_payments) + 1
            self._mock_payments.append(payment)
            return payment

        try:
            async with httpx.AsyncClient() as client:
                payload = payment.model_dump(exclude={"id", "created_at"}, exclude_none=True)
                resp = await client.post(
                    f"{self.base_url}/rest/v1/payments",
                    headers=self.headers,
                    json=payload,
                    timeout=5.0
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    if data:
                        return PaymentModel(**data[0])
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            payment.id = len(self._mock_payments) + 1
            self._mock_payments.append(payment)
            return payment
        return None

    async def get_payment_by_id(self, payment_id: int) -> Optional[PaymentModel]:
        if not self._is_configured():
            for p in self._mock_payments:
                if p.id == payment_id:
                    return p
            return None

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/rest/v1/payments?id=eq.{payment_id}&select=*",
                    headers=self.headers,
                    timeout=5.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        return PaymentModel(**data[0])
        except Exception as e:
            logger.error(f"Error getting payment {payment_id}: {e}")
        return None

    async def update_payment_status(self, payment_id: int, status: str, amount: Optional[int] = None) -> bool:
        if not self._is_configured():
            for p in self._mock_payments:
                if p.id == payment_id:
                    p.status = status
                    if amount is not None:
                        p.amount = amount
                    return True
            return False

        try:
            async with httpx.AsyncClient() as client:
                payload = {"status": status}
                if amount is not None:
                    payload["amount"] = amount
                resp = await client.patch(
                    f"{self.base_url}/rest/v1/payments?id=eq.{payment_id}",
                    headers=self.headers,
                    json=payload,
                    timeout=5.0
                )
                return resp.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Error updating payment {payment_id}: {e}")
            return False

    async def get_top_referrers(self, limit: int = 10) -> List[UserModel]:
        if not self._is_configured():
            users = list(self._mock_users.values())
            users.sort(key=lambda u: u.referral_count, reverse=True)
            return users[:limit]

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/rest/v1/users?order=referral_count.desc&limit={limit}&select=*",
                    headers=self.headers,
                    timeout=5.0
                )
                if resp.status_code == 200:
                    return [UserModel(**item) for item in resp.json()]
        except Exception as e:
            logger.error(f"Error getting top referrers: {e}")
        return []

    async def get_admin_stats(self) -> Dict[str, Any]:
        if not self._is_configured():
            return {
                "total_users": len(self._mock_users),
                "total_orders": len(self._mock_orders),
                "pending_payments": len([p for p in self._mock_payments if p.status == "Pending"]),
            }

        try:
            async with httpx.AsyncClient() as client:
                # Count users
                u_resp = await client.get(f"{self.base_url}/rest/v1/users?select=count", headers={**self.headers, "Prefer": "count=exact"}, timeout=5.0)
                total_users = int(u_resp.headers.get("content-range", "0/0").split("/")[-1]) if "content-range" in u_resp.headers else 0

                # Count orders
                o_resp = await client.get(f"{self.base_url}/rest/v1/orders?select=count", headers={**self.headers, "Prefer": "count=exact"}, timeout=5.0)
                total_orders = int(o_resp.headers.get("content-range", "0/0").split("/")[-1]) if "content-range" in o_resp.headers else 0

                # Count pending payments
                p_resp = await client.get(f"{self.base_url}/rest/v1/payments?status=eq.Pending&select=count", headers={**self.headers, "Prefer": "count=exact"}, timeout=5.0)
                pending_payments = int(p_resp.headers.get("content-range", "0/0").split("/")[-1]) if "content-range" in p_resp.headers else 0

                return {
                    "total_users": total_users,
                    "total_orders": total_orders,
                    "pending_payments": pending_payments
                }
        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            return {
                "total_users": 0,
                "total_orders": 0,
                "pending_payments": 0
            }

db = SupabaseClient()
