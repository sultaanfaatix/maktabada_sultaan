from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from database.factory import content_repo
from keyboards.common import content_list, rows_from
from utils.constants import BOOK_LEVELS, LESSON_GRADES


async def lessons_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Lessons: choose grade.", reply_markup=rows_from("lessons:grade", LESSON_GRADES))


async def lessons_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["lesson_grade"] = query.data.split(":", 2)[2]
    await query.edit_message_text("Choose subject.", reply_markup=rows_from("lessons:subject", BOOK_LEVELS["secondary"]["subjects"], back="home:lessons"))


async def lessons_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    subject = query.data.split(":", 2)[2]
    items = content_repo(context, "lessons").filter(grade=context.user_data["lesson_grade"], subject=subject)
    if not items:
        await query.edit_message_text("No lessons found for this selection.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home:lessons")]]))
        return
    await query.edit_message_text("Choose lesson.", reply_markup=content_list("lessons", items, "home:lessons"))


async def open_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    item_id = query.data.split(":")[-1]
    item = next((record for record in content_repo(context, "lessons").all() if record["id"] == item_id), None)
    if not item:
        return
    if item.get("media_type") == "video":
        await context.bot.send_video(chat_id=query.message.chat_id, video=item["file_id"], caption=item.get("title", "Lesson"))
    else:
        await context.bot.send_document(chat_id=query.message.chat_id, document=item["file_id"], caption=item.get("title", "Lesson"))


def register_lessons_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(lessons_entry, pattern=r"^home:lessons$"))
    app.add_handler(CallbackQueryHandler(lessons_grade, pattern=r"^lessons:grade:"))
    app.add_handler(CallbackQueryHandler(lessons_subject, pattern=r"^lessons:subject:"))
    app.add_handler(CallbackQueryHandler(open_lesson, pattern=r"^lessons:open:"))
