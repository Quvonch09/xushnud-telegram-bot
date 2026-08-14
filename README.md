# Turfa Seen | Rasmiy - Telegram SMM Bot (1:1 Clone)

Production-ready Telegram SMM Bot built with **Python 3.11**, **aiogram 3.10+**, **FastAPI** (Webhook / Polling), and **Supabase (PostgreSQL)**.

---

## 🌟 Features & 1:1 Flow Implementations

1. **Start & Referral Flow**:
   - Deep-linking referral parsing: `/start user{ID}`.
   - New referral awards **80 so'm** to referrer's balance, increments `referral_count`, and triggers a real-time notification.
   - Mandatory 4-channel subscription check (`getChatMember`) with `☑️ Tekshirish` verification button.

2. **Main Menu (Reply Keyboard)**:
   - 2-column layout:
     - `🛒 Buyurtma berish` | `📞 Raqam olish`
     - `🐾 Buyurtmalar` | `🙋 Pul ishlash`
     - `💎 Hisobim` | `💳 Pul kiritish`
     - `❓ Yordam` | `📚 Hamkorlik dasturi`

3. **4-Level SMM Ordering Flow (FSM)**:
   - **Level 1**: Platform selection (`Telegram`, `Instagram`, `YouTube`, `TikTok`, `📝 Barcha xizmatlar`).
   - **Level 2**: Category selection (`🔥 Reaksiya`, `👁️ Ko'rishlar`, `👤 Obunachi`, `🔊 Boost ovoz`, `🖼️ Hikoya`, `🇺🇿 O'zbek tarmoq`).
   - **Level 3**: Service list with pricing (`{name} - {price} so'm`).
   - **Level 4**: Service details (`ID`, `Price/1000`, `Min`, `Max`, `Description`).
   - **FSM Steps**: Link input (regex checked) -> Quantity input (min/max validated) -> Confirmation summary -> Balance verification & deduction -> SMM API order placement -> Real-time status receipt.
   - **Free Service**: "Tekin Obunachi" (ID 340) allows orders even with `0` balance up to max 40 quantity.

4. **Buyurtmalar**:
   - Displays user's last 10 orders with status tracking (`Pending`, `InProgress`, `Completed`, `Canceled`).

5. **Pul Ishlash (Referral) & Leaderboard**:
   - Generates custom referral link: `https://t.me/TurfaSeenBot?start=user{ID}`.
   - `🤗 TOP 10` real-time leaderboard of top referrers.

6. **Hisobim & Pul Kiritish (Deposit Flow)**:
   - Displays balance, total deposits, and user ID.
   - Multi-system deposit: `CLICK`, `PAYME`, `UZUM`, `PAYNET`.
   - Displays payment wallet (`5614684605929718`) and comment code (`8048583227`).
   - Expects screenshot upload (`F.photo`).
   - Forwards screenshot to `ADMIN_IDS` with inline `✅ Tasdiqlash` (with quick amount selection or custom amount) and `❌ Rad etish`.

7. **Admin Panel (`/admin`)**:
   - Restricted to `ADMIN_IDS`.
   - Live statistics: total users, total orders, pending payment receipts.
   - Direct balance adjustment: `/add_balance {user_id} {amount}`.
   - Channel list inspection.

8. **Production Quality**:
   - FastAPI server with `/webhook` and `/health` endpoints.
   - Graceful fallback: Automatically switches to polling mode for local development if `WEBHOOK_URL` is empty.
   - Anti-flood throttling middleware.

---

## 🚀 Setup & Deployment

### 1. Database Setup (Supabase)
1. Create a free project at [supabase.com](https://supabase.com).
2. Go to **SQL Editor** in your Supabase dashboard.
3. Open [`schema.sql`](file:///c:/Users/Bobomurodov/Desktop/telegram-bot-xushnud/schema.sql) from this repository, paste the entire SQL code, and click **Run**.
4. Copy your **Project URL** and **anon/service_role API Key** from **Project Settings -> API**.

### 2. Environment Variables (.env)
Create a `.env` file based on `.env.example`:

```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
BOT_USERNAME=TurfaSeenBot
ADMIN_IDS=8048583227,12345678

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

SMM_API_URL=https://smm-provider.com/api/v2
SMM_API_KEY=your_smm_api_key

PORT=8000
HOST=0.0.0.0
WEBHOOK_URL=https://your-app.onrender.com
WEBHOOK_PATH=/webhook

PAYMENT_CARD_NUMBER=5614684605929718
PAYMENT_COMMENT=8048583227
REFERRAL_REWARD=80
SUPPORT_ADMIN=@inqiIob
OFFICIAL_CHANNEL=@TurfaSeen
WEBSITE_URL=https://turfaseen.netlify.app
```

### 3. Local Development (Long-Polling)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the bot (Polling starts automatically if WEBHOOK_URL is not set)
python -m bot.main
```

### 4. Deploy to Render.com (Free Webhook Mode)
1. Push this project to GitHub.
2. Create a new **Web Service** on [Render.com](https://render.com).
3. Connect your GitHub repository.
4. Set:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn bot.main:app --host 0.0.0.0 --port $PORT`
5. Add your Environment Variables in Render dashboard (including `WEBHOOK_URL=https://<your-render-subdomain>.onrender.com`).
6. Deploy! Render will build the service, and the bot will register its webhook automatically on startup.

### 5. Docker Deployment
```bash
docker build -t turfa-seen-bot .
docker run -p 8000:8000 --env-file .env turfa-seen-bot
```
