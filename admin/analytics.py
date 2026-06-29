from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from admin.security import require_permission
from database.factory import analytics_repo, stats_repo

ANALYTICS_SEARCH = 810
PAGE_SIZE = 8


def analytics_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📌 Overview", callback_data="analytics:overview"), InlineKeyboardButton("📚 Content", callback_data="analytics:content")],
            [InlineKeyboardButton("⬇️ Downloads", callback_data="analytics:downloads:all:0"), InlineKeyboardButton("👥 Users", callback_data="analytics:users:0")],
            [InlineKeyboardButton("🧾 Events", callback_data="analytics:events:0"), InlineKeyboardButton("🔎 Search", callback_data="analytics:search")],
            [InlineKeyboardButton("🔙 Maamulka", callback_data="admin:menu")],
        ]
    )


@require_permission("view_statistics")
async def analytics_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    stats = stats_repo(context).snapshot()
    text = (
        "📈 Analytics Dashboard\n\n"
        f"👥 Total Users: {stats['users_total']}\n"
        f"🟢 Daily Active: {stats['daily_active_users']}\n"
        f"📚 Books: {stats['books']}   📝 Exams: {stats['exams']}\n"
        f"🎓 Lessons: {stats['lessons']}   ❓ S&J: {stats['qa']}\n\n"
        "Dooro dashboard aad rabto."
    )
    await query.edit_message_text(text, reply_markup=analytics_menu())


@require_permission("view_statistics")
async def analytics_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    stats = stats_repo(context).snapshot()
    text = (
        "📚 Content Metrics\n\n"
        f"📚 Buugaag: {stats['books']}\n"
        f"📝 Imtixaanaad: {stats['exams']}\n"
        f"🎓 Casharro: {stats['lessons']}\n"
        f"❓ S&J: {stats['qa']}\n"
        f"💬 Faallo: {stats['feedback']}\n"
        f"📊 Students: {stats['students']}"
    )
    await query.edit_message_text(text, reply_markup=analytics_menu())


@require_permission("view_statistics")
async def analytics_downloads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, _, collection, page_text = query.data.split(":")
    page = int(page_text)
    items = analytics_repo(context).downloads(None if collection == "all" else collection)
    start = page * PAGE_SIZE
    visible = items[start : start + PAGE_SIZE]
    lines = [f"{idx + start + 1}. {item['title']} [{item['collection']}] - {item['count']}" for idx, item in enumerate(visible)]
    text = "⬇️ Download Analytics\n\n" + ("\n".join(lines) if lines else "Weli downloads lama hayo.")
    await query.edit_message_text(text, reply_markup=paged_keyboard("analytics:downloads:all", page, len(items)))


@require_permission("view_statistics")
async def analytics_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[-1])
    users = analytics_repo(context).users(context.user_data.get("analytics_search", ""))
    start = page * PAGE_SIZE
    visible = users[start : start + PAGE_SIZE]
    lines = [
        f"{user['user_id']} | @{user.get('username') or '-'} | days:{len(user.get('days', []))} | last:{user.get('last_seen', '-')[:10]}"
        for user in visible
    ]
    text = "👥 User Analytics\n\n" + ("\n".join(lines) if lines else "Users lama helin.")
    await query.edit_message_text(text, reply_markup=paged_keyboard("analytics:users", page, len(users)))


@require_permission("view_statistics")
async def analytics_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[-1])
    events = analytics_repo(context).events(context.user_data.get("analytics_search", ""))
    start = page * PAGE_SIZE
    visible = events[start : start + PAGE_SIZE]
    lines = [f"{event['created_at'][:16]} | {event['name']} | {event.get('user_id')}" for event in visible]
    text = "🧾 Activity Events\n\n" + ("\n".join(lines) if lines else "Events lama helin.")
    await query.edit_message_text(text, reply_markup=paged_keyboard("analytics:events", page, len(events)))


def paged_keyboard(prefix: str, page: int, total: int) -> InlineKeyboardMarkup:
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Hore", callback_data=f"{prefix}:{page - 1}"))
    if (page + 1) * PAGE_SIZE < total:
        nav.append(InlineKeyboardButton("➡️ Xiga", callback_data=f"{prefix}:{page + 1}"))
    rows = [nav] if nav else []
    rows.append([InlineKeyboardButton("📈 Dashboard", callback_data="analytics:overview"), InlineKeyboardButton("🔙 Maamulka", callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)


@require_permission("view_statistics")
async def analytics_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔎 Analytics Search\n\nSoo qor User ID, username, event name, ama keyword.")
    return ANALYTICS_SEARCH


@require_permission("view_statistics")
async def analytics_search_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["analytics_search"] = update.message.text.strip()
    await update.message.reply_text("Search filter waa la dhigay. Dooro waxa aad rabto:", reply_markup=analytics_menu())
    return ConversationHandler.END


def analytics_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(analytics_search_start, pattern=r"^analytics:search$")],
        states={ANALYTICS_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, analytics_search_text)]},
        fallbacks=[CallbackQueryHandler(analytics_home, pattern=r"^analytics:overview$")],
        per_message=False,
    )


def register_analytics_handlers(app: Application) -> None:
    app.add_handler(analytics_conversation())
    app.add_handler(CallbackQueryHandler(analytics_home, pattern=r"^(admin:stats|analytics:overview)$"))
    app.add_handler(CallbackQueryHandler(analytics_content, pattern=r"^analytics:content$"))
    app.add_handler(CallbackQueryHandler(analytics_downloads, pattern=r"^analytics:downloads:"))
    app.add_handler(CallbackQueryHandler(analytics_users, pattern=r"^analytics:users:"))
    app.add_handler(CallbackQueryHandler(analytics_events, pattern=r"^analytics:events:"))
