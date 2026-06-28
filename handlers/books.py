from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from database.factory import analytics_repo, content_repo, platform_repo
from keyboards.common import content_list, rows_from
from utils.i18n import BOOK_TYPE_LABELS, BTN_BACK


async def books_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    settings = platform_repo(context).get()
    labels = [meta["label"] for meta in settings["levels"].values()]
    await query.edit_message_text("📚 Buugaag\n\nXulo heerka waxbarasho:", reply_markup=rows_from("books:level", labels))


async def books_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    label = query.data.split(":", 2)[2]
    repo = platform_repo(context)
    level = repo.level_by_label(label)
    context.user_data["books_level"] = level
    await query.edit_message_text(f"📚 Buugaag > {label}\n\nXulo fasal:", reply_markup=rows_from("books:grade", repo.classes_for_level(level), back="home:books"))


async def books_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    grade = query.data.split(":", 2)[2]
    level = context.user_data["books_level"]
    context.user_data["books_grade"] = grade
    await query.edit_message_text(
        f"📚 Buugaag > {grade}\n\nXulo maaddo:",
        reply_markup=rows_from("books:subject", platform_repo(context).subjects_for_level(level), back="home:books"),
    )


async def books_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    subject = query.data.split(":", 2)[2]
    context.user_data["books_subject"] = subject
    settings = platform_repo(context).get()
    labels = [BOOK_TYPE_LABELS.get(item, item) for item in settings["book_types"]]
    context.user_data["book_type_map"] = dict(zip(labels, settings["book_types"]))
    await query.edit_message_text(f"📚 Buugaag > {subject}\n\nXulo nooca buugga:", reply_markup=rows_from("books:type", labels, back="home:books"))


async def books_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    label = query.data.split(":", 2)[2]
    book_type = context.user_data.get("book_type_map", {}).get(label, label)
    criteria = {
        "level": context.user_data["books_level"],
        "grade": context.user_data["books_grade"],
        "subject": context.user_data["books_subject"],
        "book_type": book_type,
    }
    items = content_repo(context, "books").filter(**criteria)
    context.user_data["books_last_items"] = [item["id"] for item in items]
    if not items:
        await query.edit_message_text(
            "📭 Buug lagama helin xulashadan.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(BTN_BACK, callback_data="home:books")]]),
        )
        return
    await query.edit_message_text("📚 Buugaag la helay:", reply_markup=content_list("books", items, "home:books"))


async def books_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[-1])
    ids = set(context.user_data.get("books_last_items", []))
    items = [item for item in content_repo(context, "books").all() if item["id"] in ids]
    await query.edit_message_text("📚 Buugaag la helay:", reply_markup=content_list("books", items, "home:books", page=page))


async def open_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    item_id = query.data.split(":")[-1]
    repo = content_repo(context, "books")
    item = next((record for record in repo.all() if record["id"] == item_id), None)
    if not item:
        await query.edit_message_text("Buugga lama helin.")
        return
    repo.increment(item_id, "downloads")
    analytics_repo(context).download("books", item)
    await context.bot.send_document(chat_id=query.message.chat_id, document=item["file_id"], caption=f"📚 {item.get('title', 'Buug')}")


async def search_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args)
    items = content_repo(context, "books").search(query)
    if not query:
        await update.message.reply_text("Isticmaal: /search_books physics form 4")
    elif not items:
        await update.message.reply_text("Buug u dhigma lama helin.")
    else:
        await update.message.reply_text(f"🔎 Waxaa la helay {len(items[:5])} buug. Waxaan dirayaa kuwa ugu horreeya.")
        for item in items[:5]:
            await update.message.reply_document(document=item["file_id"], caption=f"📚 {item.get('title', 'Buug')}")


def register_books_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(books_entry, pattern=r"^home:books$"))
    app.add_handler(CallbackQueryHandler(books_level, pattern=r"^books:level:"))
    app.add_handler(CallbackQueryHandler(books_grade, pattern=r"^books:grade:"))
    app.add_handler(CallbackQueryHandler(books_subject, pattern=r"^books:subject:"))
    app.add_handler(CallbackQueryHandler(books_type, pattern=r"^books:type:"))
    app.add_handler(CallbackQueryHandler(books_page, pattern=r"^books:page:"))
    app.add_handler(CallbackQueryHandler(open_book, pattern=r"^books:open:"))
    app.add_handler(CommandHandler("search_books", search_books))
