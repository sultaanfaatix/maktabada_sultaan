from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from database.factory import feedback_repo


async def feedback_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💬 Faallo\n\nSoo dir:\n/feedback Magacaaga | Faalladaada")


async def feedback_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw = " ".join(context.args)
    if "|" not in raw:
        await update.message.reply_text("Isticmaal: /feedback Magacaaga | Faalladaada")
        return
    name, comment = [part.strip() for part in raw.split("|", 1)]
    feedback_repo(context).add({"name": name, "comment": comment, "user_id": update.effective_user.id})
    await update.message.reply_text("Mahadsanid. Faalladaada waa la helay.")


def register_feedback_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(feedback_entry, pattern=r"^home:feedback$"))
    app.add_handler(CommandHandler("feedback", feedback_submit))
