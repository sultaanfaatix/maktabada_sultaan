from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from database.factory import content_repo
from keyboards.common import content_list, rows_from
from utils.constants import BOOK_LEVELS, EXAM_GRADES, EXAM_YEARS


async def exams_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Exams: choose grade.", reply_markup=rows_from("exams:grade", EXAM_GRADES))


async def exams_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["exam_grade"] = query.data.split(":", 2)[2]
    await query.edit_message_text("Choose year.", reply_markup=rows_from("exams:year", EXAM_YEARS, back="home:exams"))


async def exams_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["exam_year"] = query.data.split(":", 2)[2]
    subjects = BOOK_LEVELS["middle"]["subjects"] if context.user_data["exam_grade"] == "8aad" else BOOK_LEVELS["secondary"]["subjects"]
    await query.edit_message_text("Choose subject.", reply_markup=rows_from("exams:subject", subjects, back="home:exams"))


async def exams_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    subject = query.data.split(":", 2)[2]
    items = content_repo(context, "exams").filter(grade=context.user_data["exam_grade"], year=context.user_data["exam_year"], subject=subject)
    if not items:
        await query.edit_message_text("No exams found for this selection.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home:exams")]]))
        return
    await query.edit_message_text("Choose exam PDF.", reply_markup=content_list("exams", items, "home:exams"))


async def open_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    item_id = query.data.split(":")[-1]
    item = next((record for record in content_repo(context, "exams").all() if record["id"] == item_id), None)
    if item:
        await context.bot.send_document(chat_id=query.message.chat_id, document=item["file_id"], caption=item.get("title", "Exam"))


def register_exams_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(exams_entry, pattern=r"^home:exams$"))
    app.add_handler(CallbackQueryHandler(exams_grade, pattern=r"^exams:grade:"))
    app.add_handler(CallbackQueryHandler(exams_year, pattern=r"^exams:year:"))
    app.add_handler(CallbackQueryHandler(exams_subject, pattern=r"^exams:subject:"))
    app.add_handler(CallbackQueryHandler(open_exam, pattern=r"^exams:open:"))
