import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.error import TelegramError
from config import BOT_TOKEN, OWNER_ID, FORCE_CHANNELS, FORCE_CHAT_IDS, AUTO_DELETE_SECONDS
from database import db

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def check_joined(user_id: int, bot) -> bool:
    for chat_id in FORCE_CHAT_IDS:
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True


def join_keyboard():
    buttons = []
    for i, link in enumerate(FORCE_CHANNELS):
        buttons.append([InlineKeyboardButton(f"📢 Join Channel {i+1}", url=link)])
    buttons.append([InlineKeyboardButton("✅ Done! Verify Now", callback_data="verify")])
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.first_name)

    joined = await check_joined(user.id, context.bot)
    if not joined:
        await update.message.reply_text(
            f"👋 Hello <b>{user.first_name}</b>!\n\n"
            "🔒 Please join all channels below to use this bot:",
            parse_mode="HTML",
            reply_markup=join_keyboard()
        )
        return

    await update.message.reply_text(
        f"✅ Welcome <b>{user.first_name}</b>!\n\n"
        "📦 You will receive content here automatically.\n"
        "⏳ All content deletes after <b>30 minutes</b>.",
        parse_mode="HTML"
    )


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    joined = await check_joined(user.id, context.bot)
    if joined:
        await query.edit_message_text(
            f"🎉 <b>Verified! Welcome {user.first_name}!</b>\n\n"
            "📦 You will now receive all content.\n"
            "⏳ Content auto-deletes after <b>30 minutes</b>.",
            parse_mode="HTML"
        )
    else:
        await query.answer("❌ Please join all channels first!", show_alert=True)


async def auto_delete(bot, chat_id, message_id, delay):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not the owner!")
        return

    users = db.get_all_users()
    if not users:
        await update.message.reply_text("⚠️ No users yet!")
        return

    ok, fail = 0, 0
    info = await update.message.reply_text(f"📤 Sending to {len(users)} users...")

    for uid in users:
        try:
            sent = await update.message.copy(chat_id=uid)
            asyncio.create_task(auto_delete(context.bot, uid, sent.message_id, AUTO_DELETE_SECONDS))
            ok += 1
        except TelegramError:
            fail += 1

    await info.edit_text(
        f"✅ Done!\n📨 Sent: {ok}\n❌ Failed: {fail}\n⏳ Auto-delete in 30 min"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    total = db.count_users()
    await update.message.reply_text(f"📊 Total Users: <b>{total}</b>", parse_mode="HTML")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(verify, pattern="^verify$"))

    app.add_handler(MessageHandler(
        filters.User(OWNER_ID) & (
            filters.TEXT | filters.PHOTO | filters.VIDEO |
            filters.Document.ALL | filters.AUDIO | filters.Sticker.ALL
        ),
        broadcast
    ))

    logger.info("✅ Bot started successfully!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
