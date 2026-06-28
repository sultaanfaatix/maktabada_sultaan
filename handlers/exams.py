from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from database.factory import analytics_repo, content_repo, platform_repo
from keyboards.common import content_list, rows_from
from utils.i18n import BTN_BACK


async def exams_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 Imtixaanaad\n\nXulo fasalka:", reply_markup=rows_from("exams:grade", platform_repo(context).get()["exam_classes"]))


async def exams_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["exam_grade"] = query.data.split(":", 2)[2]
    await query.edit_message_text("📝 Imtixaanaad\n\nXulo sanad dugsiyeed:", reply_markup=rows_from("exams:year", platform_repo(context).get()["exam_years"], back="home:exams"))


async def exams_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    grade = context.user_data["exam_grade"]
    context.user_data["exam_year"] = query.data.split(":", 2)[2]
    level = platform_repo(context).level_for_class(grade)
    await query.edit_message_text("📝 Imtixaanaad\n\nXulo maaddo:", reply_markup=rows_from("exams:subject", platform_repo(context).subjects_for_level(level), back="home:exams"))


async def exams_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    subject = query.data.split(":", 2)[2]
    items = content_repo(context, "exams").filter(grade=context.user_data["exam_grade"], year=context.user_data["exam_year"], subject=subject)
    context.user_data["exams_last_items"] = [item["id"] for item in items]
    if not items:
        await query.edit_message_text("📭 Imtixaan lagama helin xulashadan.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(BTN_BACK, callback_data="home:exams")]]))
        return
    await query.edit_message_text("📝 Imtixaanaad la helay:", reply_markup=content_list("exams", items, "home:exams"))


async def exams_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[-1])
    ids = set(context.user_data.get("exams_last_items", []))
    items = [item for item in content_repo(context, "exams").all() if item["id"] in ids]
    await query.edit_message_text("📝 Imtixaanaad la helay:", reply_markup=content_list("exams", items, "home:exams", page=page))


async def open_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    item_id = query.data.split(":")[-1]
    repo = content_repo(context, "exams")
    item = next((record for record in repo.all() if record["id"] == item_id), None)
    if item:
        repo.increment(item_id, "downloads")
        analytics_repo(context).download("exams", item)
        await context.bot.send_document(chat_id=query.message.chat_id, document=item["file_id"], caption=f"📝 {item.get('title', 'Imtixaan')}")


def register_exams_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(exams_entry, pattern=r"^home:exams$"))
    app.add_handler(CallbackQueryHandler(exams_grade, pattern=r"^exams:grade:"))
    app.add_handler(CallbackQueryHandler(exams_year, pattern=r"^exams:year:"))
    app.add_handler(CallbackQueryHandler(exams_subject, pattern=r"^exams:subject:"))
    app.add_handler(CallbackQueryHandler(exams_page, pattern=r"^exams:page:"))
    app.add_handler(CallbackQueryHandler(open_exam, pattern=r"^exams:open:"))
