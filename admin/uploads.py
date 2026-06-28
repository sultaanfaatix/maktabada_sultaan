from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from admin.security import admin_only
from database.factory import content_repo
from keyboards.common import rows_from
from utils.constants import BOOK_LEVELS, BOOK_TYPES, EXAM_GRADES, EXAM_YEARS, LESSON_GRADES

CHOOSING_KIND, FIELD, TITLE, FILE = range(4)


@admin_only
async def start_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    kind = query.data.split(":")[-1]
    context.user_data["upload"] = {"kind": kind}
    if kind == "books":
        await query.edit_message_text("Book upload: choose level.", reply_markup=rows_from("upload:level", [meta["label"] for meta in BOOK_LEVELS.values()], back="admin:menu"))
    elif kind == "exams":
        await query.edit_message_text("Exam upload: choose grade.", reply_markup=rows_from("upload:exam_grade", EXAM_GRADES, back="admin:menu"))
    else:
        await query.edit_message_text("Lesson upload: choose grade.", reply_markup=rows_from("upload:lesson_grade", LESSON_GRADES, back="admin:menu"))
    return FIELD


@admin_only
async def upload_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data.split(":", 2)
    field, value = data[1], data[2]
    upload = context.user_data["upload"]

    if field == "level":
        level = next(key for key, meta in BOOK_LEVELS.items() if meta["label"] == value)
        upload["level"] = level
        await query.edit_message_text("Choose grade.", reply_markup=rows_from("upload:book_grade", BOOK_LEVELS[level]["grades"], back="admin:menu"))
    elif field == "book_grade":
        upload["grade"] = value
        await query.edit_message_text("Choose subject.", reply_markup=rows_from("upload:book_subject", BOOK_LEVELS[upload["level"]]["subjects"], back="admin:menu"))
    elif field == "book_subject":
        upload["subject"] = value
        await query.edit_message_text("Choose book type.", reply_markup=rows_from("upload:book_type", BOOK_TYPES, back="admin:menu"))
    elif field == "book_type":
        upload["book_type"] = value
        await query.edit_message_text("Send the title as a text message.")
        return TITLE
    elif field == "exam_grade":
        upload["grade"] = value
        await query.edit_message_text("Choose year.", reply_markup=rows_from("upload:exam_year", EXAM_YEARS, back="admin:menu"))
    elif field == "exam_year":
        upload["year"] = value
        subjects = BOOK_LEVELS["middle"]["subjects"] if upload["grade"] == "8aad" else BOOK_LEVELS["secondary"]["subjects"]
        await query.edit_message_text("Choose subject.", reply_markup=rows_from("upload:exam_subject", subjects, back="admin:menu"))
    elif field == "exam_subject":
        upload["subject"] = value
        await query.edit_message_text("Send the exam title as a text message.")
        return TITLE
    elif field == "lesson_grade":
        upload["grade"] = value
        await query.edit_message_text("Choose subject.", reply_markup=rows_from("upload:lesson_subject", BOOK_LEVELS["secondary"]["subjects"], back="admin:menu"))
    elif field == "lesson_subject":
        upload["subject"] = value
        await query.edit_message_text("Send the lesson title as a text message.")
        return TITLE
    return FIELD


@admin_only
async def upload_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["upload"]["title"] = update.message.text.strip()
    kind = context.user_data["upload"]["kind"]
    if kind == "lessons":
        await update.message.reply_text("Send the lesson PDF or video.")
    else:
        await update.message.reply_text("Send the PDF document.")
    return FILE


@admin_only
async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    upload = context.user_data["upload"]
    document = update.message.document
    video = update.message.video
    if not document and not video:
        await update.message.reply_text("Please send a Telegram document or video file.")
        return FILE
    if upload["kind"] != "lessons" and not document:
        await update.message.reply_text("Books and exams must be uploaded as PDF documents.")
        return FILE

    file_id = document.file_id if document else video.file_id
    media_type = "video" if video else "document"
    record = content_repo(context, upload["kind"]).add({**upload, "file_id": file_id, "media_type": media_type})
    context.user_data.pop("upload", None)
    await update.message.reply_text(f"Upload saved.\nID: {record['id']}")
    return ConversationHandler.END


async def cancel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("upload", None)
    await update.effective_message.reply_text("Upload cancelled.")
    return ConversationHandler.END


def upload_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_upload, pattern=r"^admin:upload:(books|exams|lessons)$")],
        states={
            FIELD: [CallbackQueryHandler(upload_field, pattern=r"^upload:")],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, upload_title)],
            FILE: [MessageHandler((filters.Document.ALL | filters.VIDEO) & ~filters.COMMAND, upload_file)],
        },
        fallbacks=[CommandHandler("cancel", cancel_upload), CallbackQueryHandler(cancel_upload, pattern=r"^admin:menu$")],
        per_message=False,
    )
