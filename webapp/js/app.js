/**
 * Telegram Mini App - Client Application Logic
 */

// Initialize Telegram WebApp SDK
const tg = window.Telegram?.WebApp || {
    ready: () => {},
    expand: () => {},
    close: () => {},
    sendData: (data) => console.log("Telegram sendData:", data),
    openTelegramLink: (url) => window.open(url, "_blank"),
    openLink: (url) => window.open(url, "_blank"),
    HapticFeedback: {
        impactOccurred: (style) => console.log("Haptic:", style),
        notificationOccurred: (type) => console.log("Haptic notification:", type),
        selectionChanged: () => console.log("Haptic selection")
    },
    BackButton: {
        show: () => {},
        hide: () => {},
        onClick: (cb) => {}
    },
    initData: "",
    initDataUnsafe: {}
};

// Notify Telegram WebApp
try {
    tg.ready();
    tg.expand();
} catch (e) {
    console.warn("Telegram WebApp initialization error:", e);
}

// App State
const state = {
    user: {
        id: 0,
        username: "Foydalanuvchi",
        firstName: "Foydalanuvchi",
        balance: 0,
        totalDeposit: 0,
        referralsCount: 0,
        referralEarnings: 0
    },
    selectedPlatform: "Telegram",
    selectedCategory: "Obunachi",
    currentView: "dashboard",
    botUsername: "TurfaSeenBot",
    supportAdmin: "quvonchbek_070",
    channelUrl: "https://t.me/quvonch_blog"
};

// Price table per 1000 items (so'm)
const servicePrices = {
    "Telegram": {
        "Obunachi": 15000,
        "Ko'rishlar": 800,
        "Reaksiya": 1200,
        "Boost ovoz": 45000
    },
    "Instagram": {
        "Obunachi": 22000,
        "Ko'rishlar": 1000,
        "Reaksiya": 8000,
        "Boost ovoz": 20000
    },
    "YouTube": {
        "Obunachi": 75000,
        "Ko'rishlar": 18000,
        "Reaksiya": 15000,
        "Boost ovoz": 30000
    },
    "TikTok": {
        "Obunachi": 35000,
        "Ko'rishlar": 1500,
        "Reaksiya": 12000,
        "Boost ovoz": 25000
    }
};

// DOM Elements
const toastEl = document.getElementById("toast");
const userNameEl = document.getElementById("user-name");
const userIdEl = document.getElementById("user-id");
const userAvatarEl = document.getElementById("user-avatar");
const userInitialsEl = document.getElementById("user-initials");
const userBalanceEl = document.getElementById("user-balance");

// Format number with spaces (e.g. 15 000)
function formatNumber(num) {
    return (num || 0).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

// Show Toast Message
function showToast(message, duration = 2500) {
    if (!toastEl) return;
    toastEl.textContent = message;
    toastEl.classList.add("show");
    setTimeout(() => {
        toastEl.classList.remove("show");
    }, duration);
}

// Trigger Haptic Feedback
function haptic(type = "light") {
    try {
        if (tg.HapticFeedback) {
            if (type === "success" || type === "error" || type === "warning") {
                tg.HapticFeedback.notificationOccurred(type);
            } else {
                tg.HapticFeedback.impactOccurred(type);
            }
        }
    } catch (e) {}
}

// Init Telegram User Data
async function initUser() {
    const tgUser = tg.initDataUnsafe?.user;
    if (tgUser) {
        state.user.id = tgUser.id;
        state.user.username = tgUser.username || `user${tgUser.id}`;
        state.user.firstName = tgUser.first_name || "Foydalanuvchi";
        
        if (tgUser.photo_url) {
            userAvatarEl.innerHTML = `<img src="${tgUser.photo_url}" alt="Avatar">`;
        } else {
            const initial = (state.user.firstName || "U").charAt(0).toUpperCase();
            userInitialsEl.textContent = initial;
        }
    }

    // Update UI elements
    userNameEl.textContent = state.user.firstName;
    userIdEl.textContent = `ID: ${state.user.id || "12345678"}`;

    // Update Account View elements
    const accUserId = document.getElementById("acc-user-id");
    if (accUserId) accUserId.textContent = state.user.id || "12345678";

    // Update Referral Link input
    const refLinkInput = document.getElementById("referral-link");
    if (refLinkInput) {
        refLinkInput.value = `https://t.me/${state.botUsername}?start=user${state.user.id || "000"}`;
    }

    // Attempt to fetch live balance & data from API
    await fetchUserData();
}

// Fetch user data from backend API
async function fetchUserData() {
    try {
        const response = await fetch(`/api/user?user_id=${state.user.id}`, {
            headers: {
                "X-Telegram-Init-Data": tg.initData || ""
            }
        });
        if (response.ok) {
            const data = await response.json();
            state.user.balance = data.balance ?? state.user.balance;
            state.user.totalDeposit = data.total_deposit ?? state.user.totalDeposit;
            state.user.referralsCount = data.referrals_count ?? 0;
            state.user.referralEarnings = data.referral_earnings ?? (state.user.referralsCount * 80);
        }
    } catch (err) {
        console.log("Using local state data (standalone mode)");
    }

    // Render User Stats in UI
    userBalanceEl.textContent = formatNumber(state.user.balance);

    const accBalance = document.getElementById("acc-balance");
    if (accBalance) accBalance.textContent = `${formatNumber(state.user.balance)} so'm`;

    const accTotalDeposit = document.getElementById("acc-total-deposit");
    if (accTotalDeposit) accTotalDeposit.textContent = `${formatNumber(state.user.totalDeposit)} so'm`;

    const refCountEl = document.getElementById("referral-count");
    if (refCountEl) refCountEl.textContent = `${state.user.referralsCount} ta`;

    const refEarnEl = document.getElementById("referral-earnings");
    if (refEarnEl) refEarnEl.textContent = `${formatNumber(state.user.referralEarnings)} so'm`;
}

// ==========================================================================
// VIEW NAVIGATION CONTROLLER
// ==========================================================================
function navigateTo(viewName) {
    haptic("light");
    
    // Hide all views
    document.querySelectorAll(".view-container").forEach(el => {
        el.classList.remove("active");
    });

    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) {
        targetView.classList.add("active");
        state.currentView = viewName;
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    // Configure Telegram BackButton
    if (viewName === "dashboard") {
        try {
            tg.BackButton?.hide();
        } catch (e) {}
    } else {
        try {
            tg.BackButton?.show();
            tg.BackButton?.onClick(() => navigateTo("dashboard"));
        } catch (e) {}
    }

    // Initialize specific view data
    if (viewName === "order") {
        calculateOrderPrice();
    } else if (viewName === "orders") {
        loadUserOrders();
    }
}

// Handle Menu Grid Button Clicks
function handleMenuClick(action) {
    haptic("medium");
    console.log(`Action triggered: ${action}`);

    // Navigate to respective view
    navigateTo(action);
}

// ==========================================================================
// 1. ORDER VIEW LOGIC
// ==========================================================================
function selectPlatform(buttonEl, platform) {
    haptic("selectionChanged");
    document.querySelectorAll("#platform-chips .chip-item").forEach(btn => btn.classList.remove("active"));
    buttonEl.classList.add("active");
    state.selectedPlatform = platform;
    calculateOrderPrice();
}

function updateServiceOptions() {
    const select = document.getElementById("service-category-select");
    if (select) {
        state.selectedCategory = select.value;
        calculateOrderPrice();
    }
}

function calculateOrderPrice() {
    const qtyInput = document.getElementById("order-quantity-input");
    const totalEl = document.getElementById("order-total-price");
    const qty = parseInt(qtyInput?.value || "0", 10);

    const pricePer1000 = servicePrices[state.selectedPlatform]?.[state.selectedCategory] || 15000;
    const total = Math.round((qty * pricePer1000) / 1000);

    if (totalEl) {
        totalEl.textContent = `${formatNumber(total)} so'm`;
    }
    return total;
}

async function submitOrder() {
    haptic("medium");
    const linkInput = document.getElementById("order-link-input");
    const qtyInput = document.getElementById("order-quantity-input");
    const link = linkInput?.value.trim();
    const qty = parseInt(qtyInput?.value || "0", 10);
    const totalCost = calculateOrderPrice();

    if (!link) {
        haptic("error");
        showToast("⚠️ Iltimos, havola (link) kiriting!");
        return;
    }

    if (qty < 10) {
        haptic("error");
        showToast("⚠️ Minimal miqdor: 10 ta");
        return;
    }

    if (state.user.balance < totalCost) {
        haptic("warning");
        showToast("❌ Hisobingizda mablag' yetarli emas!");
        setTimeout(() => navigateTo("deposit"), 1200);
        return;
    }

    showToast("⏳ Buyurtma yuborilmoqda...");

    try {
        const response = await fetch("/api/orders", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Telegram-Init-Data": tg.initData || ""
            },
            body: JSON.stringify({
                user_id: state.user.id,
                platform: state.selectedPlatform,
                category: state.selectedCategory,
                link: link,
                quantity: qty,
                price: totalCost
            })
        });

        if (response.ok) {
            state.user.balance -= totalCost;
            userBalanceEl.textContent = formatNumber(state.user.balance);
            haptic("success");
            showToast("🎉 Buyurtmangiz muvaffaqiyatli qabul qilindi!");
            if (linkInput) linkInput.value = "";
            setTimeout(() => navigateTo("orders"), 1500);
        } else {
            throw new Error("Server error");
        }
    } catch (err) {
        // Mock fallback for demonstration
        state.user.balance -= totalCost;
        userBalanceEl.textContent = formatNumber(state.user.balance);
        haptic("success");
        showToast("🎉 Buyurtma qabul qilindi!");
        if (linkInput) linkInput.value = "";
        setTimeout(() => navigateTo("orders"), 1500);
    }
}

// ==========================================================================
// 2. CONTACT / ADMIN / EXTERNAL LINKS
// ==========================================================================
function contactAdmin(reason = "help") {
    haptic("light");
    const text = encodeURIComponent(`Salom! Men botdan yozmoqdaman (${reason}).`);
    const url = `https://t.me/${state.supportAdmin}?text=${text}`;
    if (tg.openTelegramLink) {
        tg.openTelegramLink(url);
    } else {
        window.open(url, "_blank");
    }
}

function openChannel() {
    haptic("light");
    if (tg.openTelegramLink) {
        tg.openTelegramLink(state.channelUrl);
    } else {
        window.open(state.channelUrl, "_blank");
    }
}

// ==========================================================================
// 3. ORDERS LIST
// ==========================================================================
async function loadUserOrders() {
    const listEl = document.getElementById("orders-list");
    if (!listEl) return;

    try {
        const response = await fetch(`/api/orders?user_id=${state.user.id}`, {
            headers: { "X-Telegram-Init-Data": tg.initData || "" }
        });
        if (response.ok) {
            const orders = await response.json();
            if (orders && orders.length > 0) {
                listEl.innerHTML = orders.map(o => `
                    <div class="list-item">
                        <div>
                            <div class="list-item-title">${o.service_name || "Xizmat"} (${formatNumber(o.quantity)} ta)</div>
                            <div class="list-item-sub">#${o.id} • ${formatNumber(o.price)} so'm</div>
                        </div>
                        <span class="status-badge status-${(o.status || "pending").toLowerCase()}">${o.status || "Kutilmoqda"}</span>
                    </div>
                `).join("");
            }
        }
    } catch (e) {}
}

// ==========================================================================
// 4. REFERRAL
// ==========================================================================
function copyReferralLink() {
    const input = document.getElementById("referral-link");
    if (!input) return;
    navigator.clipboard.writeText(input.value).then(() => {
        haptic("success");
        showToast("✅ Taklif havolasi nusxalandi!");
    }).catch(() => {
        input.select();
        document.execCommand("copy");
        showToast("✅ Nusxalandi!");
    });
}

function shareReferralLink() {
    haptic("light");
    const link = document.getElementById("referral-link")?.value || "";
    const text = encodeURIComponent(`🚀 Ijtimoiy tarmoqlaringizni rivojlantiring! Eng arzon va sifatli SMM xizmatlari:\n${link}`);
    const shareUrl = `https://t.me/share/url?url=${link}&text=${text}`;
    if (tg.openTelegramLink) {
        tg.openTelegramLink(shareUrl);
    } else {
        window.open(shareUrl, "_blank");
    }
}

// ==========================================================================
// 6. DEPOSIT (PUL KIRITISH)
// ==========================================================================
function selectPaymentSystem(buttonEl, system) {
    haptic("selectionChanged");
    buttonEl.parentElement.querySelectorAll(".chip-item").forEach(b => b.classList.remove("active"));
    buttonEl.classList.add("active");
}

function copyCardNumber() {
    const cardEl = document.getElementById("payment-card-num");
    const rawNum = cardEl?.textContent.replace(/\s+/g, "") || "5614684605929718";
    navigator.clipboard.writeText(rawNum).then(() => {
        haptic("success");
        showToast("💳 Karta raqami nusxalandi!");
    });
}

async function submitDeposit() {
    const amountInput = document.getElementById("deposit-amount-input");
    const amount = parseInt(amountInput?.value || "0", 10);

    if (isNaN(amount) || amount < 1000) {
        haptic("error");
        showToast("⚠️ Minimal to'lov summasi: 1 000 so'm");
        return;
    }

    haptic("medium");
    showToast("⏳ To'lov so'rovi yuborilmoqda...");

    // Send action to bot or API
    try {
        if (tg.sendData) {
            tg.sendData(JSON.stringify({
                action: "deposit",
                amount: amount,
                user_id: state.user.id
            }));
        }
    } catch (e) {}

    showToast("✅ To'lov chekini botga yuboring!");
    if (amountInput) amountInput.value = "";
    setTimeout(() => navigateTo("dashboard"), 1800);
}

// Initialize on window load
window.addEventListener("DOMContentLoaded", () => {
    initUser();
});
