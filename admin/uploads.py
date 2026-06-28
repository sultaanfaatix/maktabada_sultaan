from __future__ import annotations

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from admin.security import has_permission
from database.factory import activity_repo, content_repo, platform_repo
from keyboards.common import rows_from
from utils.i18n import BOOK_TYPE_LABELS

FIELD, TITLE, FILE = range(3)
UPLOAD_PERMISSIONS = {"books": "upload_books", "exams": "upload_exams", "lessons": "upload_lessons"}


async def start_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    kind = query.data.split(":")[-1]
    if not has_permission(update, context, UPLOAD_PERMISSIONS[kind]):
        await query.answer("Ogolaansho kuma filna.", show_alert=True)
        return ConversationHandler.END
    context.user_data["upload"] = {"kind": kind}
    settings = platform_repo(context).get()
    if kind == "books":
        labels = [meta["label"] for meta in settings["levels"].values()]
        await query.edit_message_text("📚 Upload Buug\n\nXulo heer:", reply_markup=rows_from("upload:level", labels, back="admin:menu"))
    elif kind == "exams":
        await query.edit_message_text("📝 Upload Imtixaan\n\nXulo fasal:", reply_markup=rows_from("upload:exam_grade", settings["exam_classes"], back="admin:menu"))
    else:
        await query.edit_message_text("🎓 Upload Cashar\n\nXulo fasal:", reply_markup=rows_from("upload:lesson_grade", settings["lesson_classes"], back="admin:menu"))
    return FIELD


async def upload_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    field, value = query.data.split(":", 2)[1:]
    upload = context.user_data["upload"]
    repo = platform_repo(context)

    if field == "level":
        level = repo.level_by_label(value)
        upload["level"] = level
        await query.edit_message_text("Xulo fasal:", reply_markup=rows_from("upload:book_grade", repo.classes_for_level(level), back="admin:menu"))
    elif field == "book_grade":
        upload["grade"] = value
        await query.edit_message_text("Xulo maaddo:", reply_markup=rows_from("upload:book_subject", repo.subjects_for_level(upload["level"]), back="admin:menu"))
    elif field == "book_subject":
        upload["subject"] = value
        settings = repo.get()
        labels = [BOOK_TYPE_LABELS.get(item, item) for item in settings["book_types"]]
        upload["book_type_map"] = dict(zip(labels, settings["book_types"]))
        await query.edit_message_text("Xulo nooca buugga:", reply_markup=rows_from("upload:book_type", labels, back="admin:menu"))
    elif field == "book_type":
        upload["book_type"] = upload.pop("book_type_map", {}).get(value, value)
        await query.edit_message_text("Soo dir title-ka buugga.")
        return TITLE
    elif field == "exam_grade":
        upload["grade"] = value
        await query.edit_message_text("Xulo sanad dugsiyeed:", reply_markup=rows_from("upload:exam_year", repo.get()["exam_years"], back="admin:menu"))
    elif field == "exam_year":
        upload["year"] = value
        level = repo.level_for_class(upload["grade"])
        await query.edit_message_text("Xulo maaddo:", reply_markup=rows_from("upload:exam_subject", repo.subjects_for_level(level), back="admin:menu"))
    elif field == "exam_subject":
        upload["subject"] = value
        await query.edit_message_text("Soo dir title-ka imtixaanka.")
        return TITLE
    elif field == "lesson_grade":
        upload["grade"] = value
        level = repo.level_for_class(value)
        await query.edit_message_text("Xulo maaddo:", reply_markup=rows_from("upload:lesson_subject", repo.subjects_for_level(level), back="admin:menu"))
    elif field == "lesson_subject":
        upload["subject"] = value
        await query.edit_message_text("Soo dir title-ka casharka.")
        return TITLE
    return FIELD


async def upload_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["upload"]["title"] = update.message.text.strip()
    kind = context.user_data["upload"]["kind"]
    await update.message.reply_text("Soo dir PDF ama video." if kind == "lessons" else "Soo dir PDF document.")
    return FILE


async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    upload = context.user_data["upload"]
    document = update.message.document
    video = update.message.video
    if not document and not video:
        await update.message.reply_text("Fadlan soo dir document ama video.")
        return FILE
    if upload["kind"] != "lessons" and not document:
        await update.message.reply_text("Buugaag iyo imtixaanno waa inay PDF/document noqdaan.")
        return FILE

    file_id = document.file_id if document else video.file_id
    media_type = "video" if video else "document"
    record = content_repo(context, upload["kind"]).add({**upload, "file_id": file_id, "media_type": media_type})
    activity_repo(context).log(update.effective_user.id, "upload", {"collection": upload["kind"], "id": record["id"]})
    context.user_data.pop("upload", None)
    await update.message.reply_text(f"Upload waa la keydiyay.\nID: {record['id']}")
    return ConversationHandler.END


async def cancel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("upload", None)
    await update.effective_message.reply_text("Upload waa la joojiyay.")
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
