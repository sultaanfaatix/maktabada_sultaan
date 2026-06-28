from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from database.factory import content_repo
from keyboards.common import content_list, rows_from
from utils.constants import BOOK_LEVELS, BOOK_TYPES


async def books_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("BUUGAAG: Xulo Heer.", reply_markup=rows_from("books:level", [v["label"] for v in BOOK_LEVELS.values()]))


async def books_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    label = query.data.split(":", 2)[2]
    level = next(key for key, meta in BOOK_LEVELS.items() if meta["label"] == label)
    context.user_data["books_level"] = level
    await query.edit_message_text(f"{label}: choose grade.", reply_markup=rows_from("books:grade", BOOK_LEVELS[level]["grades"], back="home:books"))


async def books_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    grade = query.data.split(":", 2)[2]
    level = context.user_data["books_level"]
    context.user_data["books_grade"] = grade
    await query.edit_message_text("Choose subject.", reply_markup=rows_from("books:subject", BOOK_LEVELS[level]["subjects"], back="home:books"))


async def books_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    subject = query.data.split(":", 2)[2]
    context.user_data["books_subject"] = subject
    await query.edit_message_text("Choose book type.", reply_markup=rows_from("books:type", BOOK_TYPES, back="home:books"))


async def books_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    book_type = query.data.split(":", 2)[2]
    criteria = {
        "level": context.user_data["books_level"],
        "grade": context.user_data["books_grade"],
        "subject": context.user_data["books_subject"],
        "book_type": book_type,
    }
    items = content_repo(context, "books").filter(**criteria)
    if not items:
        await query.edit_message_text("No books found for this selection.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home:books")]]))
        return
    await query.edit_message_text("Choose a book.", reply_markup=content_list("books", items, "home:books"))


async def open_book(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    item_id = query.data.split(":")[-1]
    item = next((record for record in content_repo(context, "books").all() if record["id"] == item_id), None)
    if not item:
        await query.edit_message_text("Book not found.")
        return
    await context.bot.send_document(chat_id=query.message.chat_id, document=item["file_id"], caption=item.get("title", "Book"))


async def search_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args)
    items = content_repo(context, "books").search(query)
    if not query:
        await update.message.reply_text("Usage: /search_books physics form 4")
    elif not items:
        await update.message.reply_text("No matching books found.")
    else:
        await update.message.reply_text(f"Found {len(items[:5])} book(s). Sending the first matches.")
        for item in items[:5]:
            await update.message.reply_document(document=item["file_id"], caption=item.get("title", "Book"))


def register_books_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(books_entry, pattern=r"^home:books$"))
    app.add_handler(CallbackQueryHandler(books_level, pattern=r"^books:level:"))
    app.add_handler(CallbackQueryHandler(books_grade, pattern=r"^books:grade:"))
    app.add_handler(CallbackQueryHandler(books_subject, pattern=r"^books:subject:"))
    app.add_handler(CallbackQueryHandler(books_type, pattern=r"^books:type:"))
    app.add_handler(CallbackQueryHandler(open_book, pattern=r"^books:open:"))
    app.add_handler(CommandHandler("search_books", search_books))
