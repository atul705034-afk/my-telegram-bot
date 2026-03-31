# 🤖 Telegram Content Bot — Setup Guide

## 📁 Files
```
telegram_bot/
├── bot.py           ← Main bot code
├── config.py        ← YOUR SETTINGS (edit this!)
├── database.py      ← Auto user storage
└── requirements.txt ← Dependencies
```

---

## ✅ STEP 1 — Create Your Bot

1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Give it a name and username
4. Copy the **Bot Token** it gives you

---

## ✅ STEP 2 — Get Your Owner ID

1. Open Telegram → search **@userinfobot**
2. Send `/start`
3. Copy your **numeric ID** (e.g. 987654321)

---

## ✅ STEP 3 — Edit config.py

Open `config.py` and fill in:

```python
BOT_TOKEN = "1234567890:ABCDefgh..."     # from BotFather
OWNER_ID  = 987654321                    # your numeric ID

FORCE_CHANNELS = [
    "@your_channel_1",
    "@your_channel_2",
    "@your_channel_3",
    "@your_channel_4",
]
```

> ⚠️ Make sure your bot is an **Admin** in each force-join channel!

---

## ✅ STEP 4 — Install & Run

### Option A — Run on your PC / Server
```bash
# Install Python 3.10+ if not installed

pip install -r requirements.txt
python bot.py
```

### Option B — Run FREE on Koyeb / Railway / Render
1. Upload all 4 files to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Set start command: `python bot.py`
4. Done! It runs 24/7 for free.

---

## 🎮 How To Use (As Owner)

| Action | What happens |
|--------|-------------|
| Send any photo | Broadcasts to ALL users, auto-deletes in 30 min |
| Send any video | Same as above |
| Send any file/APK | Same as above |
| Send a link | Same as above |
| `/broadcast text` | Send custom text to all users |
| `/stats` | See total user count |

---

## 👤 How It Works For Users

1. User opens bot → must **join all 4 channels** first
2. After joining → clicks **✅ Verify** button
3. Now they receive everything you share
4. All content **auto-deletes after 30 minutes** ⏳

---

## ⚠️ Important Notes

- Bot must be **Admin** in all force-join channels
- Users who block the bot are automatically skipped in broadcasts
- The `users.db` file stores all users locally
