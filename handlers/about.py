from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from database.factory import about_repo, stats_repo


def about_nav() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👤 Aasaasaha", callback_data="about:founder"), InlineKeyboardButton("🎯 Mission", callback_data="about:mission")],
            [InlineKeyboardButton("☎️ Xidhiidh", callback_data="about:contact"), InlineKeyboardButton("📊 Stats", callback_data="about:stats")],
            [InlineKeyboardButton("🔙 Dib-u-noqo", callback_data="home:menu")],
        ]
    )


async def about_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    profile = about_repo(context).get()
    text = (
        f"ℹ️ {profile['organization']}\n\n"
        f"{profile['description']}\n\n"
        "Dooro qaybta aad rabto inaad eegto:"
    )
    if profile.get("logo_file_id"):
        await query.message.reply_photo(photo=profile["logo_file_id"], caption=text, reply_markup=about_nav())
    else:
        await query.edit_message_text(text, reply_markup=about_nav())


async def about_founder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    profile = about_repo(context).get()
    text = f"👤 Founder Profile\n\nMagac: {profile['founder_name']}\nDoorka: {profile['founder_title']}\nUrur: {profile['organization']}"
    if profile.get("photo_file_id"):
        await query.message.reply_photo(photo=profile["photo_file_id"], caption=text, reply_markup=about_nav())
    else:
        await query.edit_message_text(text, reply_markup=about_nav())


async def about_mission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    profile = about_repo(context).get()
    await query.edit_message_text(f"🎯 Mission\n\n{profile['mission']}", reply_markup=about_nav())


async def about_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    profile = about_repo(context).get()
    contact = profile["contact"]
    links = "\n".join(f"{name}: {url}" for name, url in profile["social_links"].items())
    await query.edit_message_text(
        f"☎️ Contact\n\nPhone: {contact['phone']}\nEmail: {contact['email']}\nTelegram: {contact['telegram']}\n\n🌐 Social Links\n{links}",
        reply_markup=about_nav(),
    )


async def about_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    stats = stats_repo(context).snapshot()
    text = (
        "📊 Platform Summary\n\n"
        f"📚 Buugaag: {stats['books']}\n"
        f"📝 Imtixaanaad: {stats['exams']}\n"
        f"🎓 Casharro: {stats['lessons']}\n"
        f"❓ S&J: {stats['qa']}\n"
        f"👥 Users: {stats['users_total']}"
    )
    await query.edit_message_text(text, reply_markup=about_nav())


def register_about_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(about_home, pattern=r"^about:home$"))
    app.add_handler(CallbackQueryHandler(about_founder, pattern=r"^about:founder$"))
    app.add_handler(CallbackQueryHandler(about_mission, pattern=r"^about:mission$"))
    app.add_handler(CallbackQueryHandler(about_contact, pattern=r"^about:contact$"))
    app.add_handler(CallbackQueryHandler(about_stats, pattern=r"^about:stats$"))
