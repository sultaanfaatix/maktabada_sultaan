from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from keyboards.common import main_menu


def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user

    settings = context.bot_data.get("settings")
    if not settings:
        return False

    return bool(user and user.id == settings.admin_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Welcome to MAKTABADA SULTAAN v2.\nChoose a service:",
        reply_markup=main_menu(is_admin(update, context)),
    )


async def home_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "MAKTABADA SULTAAN v2\nChoose a service:",
        reply_markup=main_menu(is_admin(update, context)),
    )


def register_start_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CallbackQueryHandler(home_menu, pattern=r"^home:menu$"))