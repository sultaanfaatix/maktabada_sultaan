from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from admin.security import is_admin
from database.factory import analytics_repo, content_repo
from keyboards.common import bottom_menu, main_menu
from utils.i18n import (
    APP_NAME,
    BTN_ADMIN,
    BTN_BOOKS,
    BTN_EXAMS,
    BTN_FEEDBACK,
    BTN_LESSONS,
    BTN_PROFILE,
    BTN_QA,
    BTN_RESULTS,
    BTN_SETTINGS,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    analytics_repo(context).track_user(update.effective_user.id, update.effective_user.username)
    await update.effective_message.reply_text(
        f"{APP_NAME}\n\nAdeeg dooro:",
        reply_markup=main_menu(is_admin(update, context)),
    )
    await update.effective_message.reply_text(
        "Menu-ga hoose wuxuu kuu fududeynayaa inaad si dhaqso ah u furto adeeg kasta.",
        reply_markup=bottom_menu(is_admin(update, context)),
    )


async def home_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    analytics_repo(context).track_user(query.from_user.id, query.from_user.username)
    await query.edit_message_text(
        f"{APP_NAME}\n\nAdeeg dooro:",
        reply_markup=main_menu(is_admin(update, context)),
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    analytics_repo(context).track_user(user.id, user.username)
    role = "Admin" if is_admin(update, context) else "User"
    await update.effective_message.reply_text(
        f"👤 Profile\n\nMagac: {user.full_name}\nUser ID: {user.id}\nHeer: {role}",
        reply_markup=bottom_menu(is_admin(update, context)),
    )


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "⚙️ Settings\n\nLuqadda: Afsoomaali\nNavigation: Persistent Menu + Inline Menu\nSearch: /search eray",
        reply_markup=bottom_menu(is_admin(update, context)),
    )


async def global_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("Isticmaal: /search fasal ama maaddo ama sanad")
        return
    results = []
    for collection, label in [("books", "Buug"), ("exams", "Imtixaan"), ("lessons", "Cashar"), ("qa", "S&J")]:
        for item in content_repo(context, collection).search(query)[:5]:
            title = item.get("title", item.get("question", item["id"]))
            results.append(f"{label}: {title} ({item['id']})")
    if not results:
        await update.message.reply_text("Wax natiijo ah lama helin.")
        return
    await update.message.reply_text("🔎 Natiijooyinka raadinta:\n\n" + "\n".join(results[:20]))


async def bottom_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    analytics_repo(context).track_user(update.effective_user.id, update.effective_user.username)
    if text == BTN_PROFILE:
        await profile(update, context)
    elif text == BTN_SETTINGS:
        await settings(update, context)
    elif text == BTN_RESULTS:
        await update.message.reply_text("📊 Natiijooyin\n\nIsticmaal: /result STUDENT_ID", reply_markup=bottom_menu(is_admin(update, context)))
    elif text == BTN_FEEDBACK:
        await update.message.reply_text("💬 Faallo\n\nIsticmaal: /feedback Magac | Fariin", reply_markup=bottom_menu(is_admin(update, context)))
    elif text in {BTN_BOOKS, BTN_EXAMS, BTN_LESSONS, BTN_QA, BTN_ADMIN}:
        await update.message.reply_text("Adeeg dooro:", reply_markup=main_menu(is_admin(update, context)))


async def callback_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    role = "Admin" if is_admin(update, context) else "User"
    await query.edit_message_text(f"👤 Profile\n\nMagac: {user.full_name}\nUser ID: {user.id}\nHeer: {role}", reply_markup=main_menu(is_admin(update, context)))


async def callback_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚙️ Settings\n\nLuqadda: Afsoomaali\nNavigation: Persistent Menu + Inline Menu", reply_markup=main_menu(is_admin(update, context)))


def register_start_handlers(app: Application) -> None:
    app.add_handler(CommandHandler(["start", "menu"], start))
    app.add_handler(CommandHandler("search", global_search))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CallbackQueryHandler(home_menu, pattern=r"^home:menu$"))
    app.add_handler(CallbackQueryHandler(callback_profile, pattern=r"^home:profile$"))
    app.add_handler(CallbackQueryHandler(callback_settings, pattern=r"^home:settings$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bottom_menu_router), group=9)
