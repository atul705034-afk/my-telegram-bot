import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMemberUpdated
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ChatMemberHandler
)
from telegram.error import TelegramError
from config import (
    BOT_TOKEN, OWNER_ID, FORCE_CHANNELS, AUTO_DELETE_SECONDS
)
from database import db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

async def is_user_joined(user_id: int, bot) -> bool:
    """Check if user has joined all force-join channels."""
    for channel in FORCE_CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except TelegramError:
            return False
    return True


def build_force_join_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard with channel join buttons + verify button."""
    buttons = []
    row = []
    for i, channel in enumerate(FORCE_CHANNELS):
        row.append(InlineKeyboardButton(
            text=f"📢 Join Channel {i+1}",
            url=f"https://t.me/{channel.lstrip('@')}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("✅ I've Joined — Verify", callback_data="verify_join")])
    return InlineKeyboardMarkup(buttons)


async def schedule_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
    """Delete a message after AUTO_DELETE_SECONDS."""
    await asyncio.sleep(AUTO_DELETE_SECONDS)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramError:
        pass


# ─────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username or user.first_name)

    if not await is_user_joined(user.id, context.bot):
        msg = await update.message.reply_text(
            f"👋 Hey <b>{user.first_name}</b>!\n\n"
            "🔒 To use this bot, please join all channels below first:",
            parse_mode="HTML",
            reply_markup=build_force_join_keyboard()
        )
        return

    await update.message.reply_text(
        f"✅ Welcome back, <b>{user.first_name}</b>!\n\n"
        "📦 You will receive all shared content here.\n"
        "⏳ All content auto-deletes after <b>30 minutes</b>.",
        parse_mode="HTML"
    )


# ─────────────────────────────────────────────
#  Verify join callback
# ─────────────────────────────────────────────

async def verify_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if await is_user_joined(user.id, context.bot):
        await query.edit_message_text(
            f"🎉 <b>Verified!</b> Welcome, {user.first_name}!\n\n"
            "📦 You will now receive all content shared by the owner.\n"
            "⏳ Content auto-deletes after <b>30 minutes</b>.",
            parse_mode="HTML"
        )
    else:
        await query.answer("❌ You haven't joined all channels yet!", show_alert=True)


# ─────────────────────────────────────────────
#  OWNER BROADCAST — any message from owner
# ─────────────────────────────────────────────

async def owner_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When owner sends any message, broadcast to all users."""
    user = update.effective_user
    if user.id != OWNER_ID:
        # Non-owner users just get a gentle message
        await update.message.reply_text(
            "ℹ️ This bot is for receiving content only. Sit tight!"
        )
        return

    users = db.get_all_users()
    if not users:
        await update.message.reply_text("⚠️ No users in database yet.")
        return

    success, failed = 0, 0
    status_msg = await update.message.reply_text(f"📤 Broadcasting to {len(users)} users...")

    sent_messages = {}  # user_id -> message_id (for auto-delete)

    for uid in users:
        try:
            sent = await update.message.copy(chat_id=uid)
            sent_messages[uid] = sent.message_id
            success += 1
        except TelegramError as e:
            logger.warning(f"Failed to send to {uid}: {e}")
            failed += 1

    await status_msg.edit_text(
        f"✅ Broadcast done!\n"
        f"• Delivered: {success}\n"
        f"• Failed: {failed}\n"
        f"⏳ Messages will auto-delete in 30 minutes."
    )

    # Schedule deletion for all sent messages
    for uid, mid in sent_messages.items():
        asyncio.create_task(schedule_delete(context, uid, mid))


# ─────────────────────────────────────────────
#  /stats  (owner only)
# ─────────────────────────────────────────────

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    total = db.count_users()
    await update.message.reply_text(
        f"📊 <b>Bot Stats</b>\n\n"
        f"👥 Total Users: <b>{total}</b>\n"
        f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        parse_mode="HTML"
    )


# ─────────────────────────────────────────────
#  /broadcast  (send a custom text broadcast)
# ─────────────────────────────────────────────

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast Your message here")
        return

    text = " ".join(context.args)
    users = db.get_all_users()
    success, failed = 0, 0

    for uid in users:
        try:
            msg = await context.bot.send_message(chat_id=uid, text=text)
            asyncio.create_task(schedule_delete(context, uid, msg.message_id))
            success += 1
        except TelegramError:
            failed += 1

    await update.message.reply_text(f"✅ Sent: {success} | ❌ Failed: {failed}")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CallbackQueryHandler(verify_join_callback, pattern="^verify_join$"))

    # Owner sends any media/text → broadcast to all
    app.add_handler(MessageHandler(
        filters.User(OWNER_ID) & (
            filters.TEXT | filters.PHOTO | filters.VIDEO |
            filters.Document.ALL | filters.AUDIO
        ),
        owner_broadcast
    ))

    logger.info("Bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
