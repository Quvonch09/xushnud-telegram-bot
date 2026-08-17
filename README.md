# 🚀 Turfa Seen | Telegram Bot & Telegram Mini App (Web App)

Zamonaviy **Telegram Mini App (Web App)** va **Python (aiogram 3.x) + FastAPI** asosidagi to'liq integratsiyalangan Telegram bot tizimi.

Ushbu loyihada Telegramning standart klaviaturalaridan farqli ravishda, **har bir button rangi CSS orqali erkin boshqariladigan**, moslashuvchan (responsive) va zamonaviy Telegram Mini App yaratilgan.

---

## 📸 Mini App Interfeysi va Joylashuvi

Mini App quyidagi 2 ustunli (grid) qulay interfeysga ega:

```text
┌──────────────────────────────────────────────────┐
│                                                  │
│   👤 [Avatar] Foydalanuvchi                      │
│   💰 Balans: 15 000 so'm       [➕ To'ldirish]    │
│                                                  │
│   🛒 Buyurtma berish     📞 Raqam olish          │
│   (Custom CSS: Binafsha) (Custom CSS: Moviy)     │
│                                                  │
│   🛍️ Buyurtmalar         🤑 Pul ishlash          │
│   (Custom CSS: Firuza)   (Custom CSS: Yashil)    │
│                                                  │
│   💎 Hisobim             💳 Pul kiritish         │
│   (Custom CSS: To'q pushti) (Custom CSS: To'q sariq)│
│                                                  │
│   ❓ Yordam              💻 Hamkorlik            │
│   (Custom CSS: Kulrang)  (Custom CSS: Pushti)    │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## 🎨 Button Ranglarini O'zgartirish (Custom CSS)

Buttonlarning ranglari `webapp/css/style.css` faylidagi `:root` CSS o'zgaruvchilari orqali boshqariladi.

Siz istalgan vaqtda ularni o'zingiz xohlagan **HEX**, **RGB** yoki **linear-gradient** ranglariga o'zgartirishingiz mumkin:

```css
/* webapp/css/style.css */
:root {
    /* 8 TA ASOSIY TUGMA RANGLARI */
    --color-order: linear-gradient(135deg, #7C3AED, #9333EA);       /* 🛒 Buyurtma berish */
    --color-phone: linear-gradient(135deg, #2563EB, #3B82F6);       /* 📞 Raqam olish */
    --color-orders: linear-gradient(135deg, #0891B2, #06B6D4);      /* 🛍️ Buyurtmalar */
    --color-money: linear-gradient(135deg, #16A34A, #22C55E);       /* 🤑 Pul ishlash */
    --color-account: linear-gradient(135deg, #9333EA, #C026D3);     /* 💎 Hisobim */
    --color-deposit: linear-gradient(135deg, #EA580C, #F97316);     /* 💳 Pul kiritish */
    --color-help: linear-gradient(135deg, #475569, #64748B);        /* ❓ Yordam */
    --color-partner: linear-gradient(135deg, #DB2777, #EC4899);     /* 💻 Hamkorlik dasturi */
}
```

Oddiy qizil yoki boshqa rang qilish misoli:
```css
--color-order: #FF0000;
--color-phone: #00FF00;
```

---

## 📁 Loyiha Strukturasi

```text
telegram-mini-app/
│
├── bot/
│   ├── main.py                     # FastAPI Web Application & Bot Lifespan
│   ├── config.py                   # Pydantic Settings & WebApp URL
│   ├── states.py                   # FSM Holatlari
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py               # Mini App uchun REST API (/api/user, /api/orders, /api/deposit)
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── telegram_auth.py        # Telegram initData HMAC-SHA256 xavfsizlik tekshiruvi
│   │
│   ├── handlers/
│   │   ├── start.py                # /start, WebApp inline button & web_app_data qabul qiluvchi
│   │   ├── main_menu.py            # Asosiy menyu
│   │   ├── orders.py               # SMM buyurtma berish logikasi
│   │   ├── payments.py             # To'lov va hisob
│   │   ├── referral.py             # Referal dasturi
│   │   └── admin.py                # Admin boshqaruv paneli
│   │
│   ├── database/                   # Supabase / PostgreSQL mijozlari va modellari
│   ├── keyboards/                  # Inline va Reply klaviaturalar
│   └── middlewares/                # Throttling & Majburiy obuna tekshiruvlari
│
├── webapp/                         # Telegram Mini App Frontend
│   ├── index.html                  # Responsive HTML5 UI (8 buttons & views)
│   ├── css/
│   │   └── style.css               # Customizable CSS o'zgaruvchilari va Dark/Light theme
│   └── js/
│       └── app.js                  # Telegram WebApp JS SDK, Haptics, BackButton, API
│
├── nginx.conf.example              # Production Nginx HTTPS konfiguratsiyasi
├── requirements.txt                # Python dependencylar
├── schema.sql                      # Database jadvallari
├── .env.example                    # Muhit o'zgaruvchilari namunasi
└── README.md                       # Qo'llanma
```

---

## ⚙️ O'rnatish va Ishga Tushirish

### 1. Virtual Muhit Yaratish va Aktivlashtirish

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Dependencylarni O'rnatish

```bash
pip install -r requirements.txt
```

### 3. `.env` Faylini Sozlash

`.env.example` faylidan `.env` nusxasini yarating va qiymatlarni kiriting:

```env
BOT_TOKEN=8883327795:AAHp9pyJtvdCugKsHMtC5pgKpurDQWdby_M
BOT_USERNAME=Xushnud_01_bot
ADMIN_IDS=8048583227

# Mini App URL (HTTPS bo'lishi shart)
WEBAPP_URL=https://your-domain.com/webapp
WEBSITE_URL=https://turfaseen.netlify.app

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key

PORT=8000
HOST=0.0.0.0
```

### 4. Bot va Serverni Ishga Tushirish

```bash
python -m bot.main
```
Server `http://0.0.0.0:8000` portida ishga tushadi:
- Mini App: `http://localhost:8000/webapp/` yoki `http://localhost:8000/`
- API Health: `http://localhost:8000/health`
- REST API: `http://localhost:8000/api/*`

---

## 🌐 Localhost'da Mini App'ni Test Qilish (HTTPS Tunnel)

Telegram Mini App faqat **HTTPS** protokoli orqali ishlaydi. Local rivojlantirish uchun tunnel dasturlaridan foydalaning:

### Variant A: Cloudflare Tunnel (Tavsiya etiladi, mutlaqo bepul)
```bash
cloudflared tunnel --url http://localhost:8000
```
Natijada berilgan `https://random-id.trycloudflare.com` havolasini `.env` faylidagi `WEBAPP_URL` ga kiriting:
```env
WEBAPP_URL=https://random-id.trycloudflare.com/webapp
```

### Variant B: ngrok
```bash
ngrok http 8000
```
Berilgan `https://xxxx.ngrok-free.app` havolasini `WEBAPP_URL` ga yozing.

---

## 🤖 BotFather Orqali Menu Button Sozlash

1. Telegramda [@BotFather](https://t.me/BotFather) botiga o'ting.
2. `/mybots` buyrug'ini yuboring va o'z botingizni tanlang.
3. **Bot Settings** -> **Menu Button** -> **Configure menu button** bo'limiga kiring.
4. Mini App havolangizni yuboring: `https://your-domain.com/webapp`
5. Menu button sarlavhasi sifatida yozing: `🚀 Ilova`

> *Eslatma: Bot ishga tushganda `aiogram` kodi avtomatik ravishda `bot.set_chat_menu_button` orqali ham buni sozlaydi.*

---

## 🔒 Xavfsizlik va Telegram `initData` Validatsiyasi

Frontenddan kelayotgan so'rovlar `bot/utils/telegram_auth.py` ichidagi HMAC-SHA256 algoritmi orqali `BOT_TOKEN` yordamida tekshiriladi. Faqat Telegram tomonidan imzolangan haqiqiy foydalanuvchilar ma'lumotlariga ruxsat beriladi.

---

## 🚀 Production Deployment (Nginx + HTTPS)

`nginx.conf.example` faylidan foydalanib, serveringizda Nginx va Certbot (Let's Encrypt) orqali HTTPS SSL o'rnating.

```bash
# Nginx faylini nusxalash
sudo cp nginx.conf.example /etc/nginx/sites-available/mini-app.conf
sudo ln -s /etc/nginx/sites-available/mini-app.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# SSL sertifikat olish
sudo certbot --nginx -d app.example.uz
```
