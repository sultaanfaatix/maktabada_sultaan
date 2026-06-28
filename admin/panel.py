from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from admin.security import admin_only
from admin.uploads import upload_conversation
from database.factory import content_repo, feedback_repo, results_repo, stats_repo


def admin_menu_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Upload Book", callback_data="admin:upload:books")],
            [InlineKeyboardButton("Upload Exam", callback_data="admin:upload:exams")],
            [InlineKeyboardButton("Upload Lesson", callback_data="admin:upload:lessons")],
            [InlineKeyboardButton("Manage Results", callback_data="admin:results_help"), InlineKeyboardButton("Manage Q&A", callback_data="admin:qa_help")],
            [InlineKeyboardButton("Delete Content", callback_data="admin:delete_help")],
            [InlineKeyboardButton("Statistics", callback_data="admin:stats"), InlineKeyboardButton("Feedback", callback_data="admin:feedback")],
            [InlineKeyboardButton("Back", callback_data="home:menu")],
        ]
    )


@admin_only
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("Admin Panel", reply_markup=admin_menu_markup())


@admin_only
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Admin Panel", reply_markup=admin_menu_markup())


@admin_only
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    stats = stats_repo(context).snapshot()
    await query.edit_message_text("\n".join(f"{key.title()}: {value}" for key, value in stats.items()), reply_markup=admin_menu_markup())


@admin_only
async def admin_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    items = feedback_repo(context).all()[-10:]
    if not items:
        await query.edit_message_text("No feedback yet.", reply_markup=admin_menu_markup())
        return
    text = "\n\n".join(f"{item['id']} | {item['name']}\n{item['comment']}" for item in items)
    await query.edit_message_text(f"Latest feedback:\n\n{text}\n\nDelete: /delete_feedback ID", reply_markup=admin_menu_markup())


@admin_only
async def admin_results_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Manage Results\n\n"
        "Use:\n"
        "/set_result STUDENT_ID | Name | Grade | Exam Type | Subject | Score | Max\n\n"
        "Example:\n"
        "/set_result F4-001 | Ahmed Ali | Form 4 | Final Exam | Mathematics | 92 | 100",
        reply_markup=admin_menu_markup(),
    )


@admin_only
async def admin_qa_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Manage Q&A\n\n"
        "Use:\n"
        "/add_qa Grade | Subject | Question | Answer | choice A ; choice B ; choice C\n\n"
        "For text questions, put the answer and leave choices as a short note.",
        reply_markup=admin_menu_markup(),
    )


@admin_only
async def admin_delete_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Delete Content\n\n"
        "/delete_content books|exams|lessons|qa CONTENT_ID\n"
        "/delete_feedback FEEDBACK_ID",
        reply_markup=admin_menu_markup(),
    )


@admin_only
async def delete_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /delete_feedback FEEDBACK_ID")
        return
    deleted = feedback_repo(context).delete(context.args[0])
    await update.message.reply_text("Feedback deleted." if deleted else "Feedback not found.")


@admin_only
async def delete_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2 or context.args[0] not in {"books", "exams", "lessons", "qa"}:
        await update.message.reply_text("Usage: /delete_content books|exams|lessons|qa CONTENT_ID")
        return
    deleted = content_repo(context, context.args[0]).delete(context.args[1])
    await update.message.reply_text("Content deleted." if deleted else "Content not found.")


@admin_only
async def set_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw = update.message.text.removeprefix("/set_result").strip()
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) != 7:
        await update.message.reply_text("Usage: /set_result STUDENT_ID | Name | Grade | Exam Type | Subject | Score | Max")
        return
    sid, name, grade, exam_type, subject, score, max_score = parts
    try:
        score_value = float(score)
        max_value = float(max_score)
    except ValueError:
        await update.message.reply_text("Score and Max must be numbers.")
        return
    results_repo(context).upsert_score(sid, name, grade, exam_type, subject, score_value, max_value)
    await update.message.reply_text("Result saved.")


@admin_only
async def add_qa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw = update.message.text.removeprefix("/add_qa").strip()
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) < 5:
        await update.message.reply_text("Usage: /add_qa Grade | Subject | Question | Answer | choice A ; choice B ; choice C")
        return
    grade, subject, question, answer, choices = parts[:5]
    record = content_repo(context, "qa").add(
        {"grade": grade, "subject": subject, "question": question, "answer": answer, "choices": [item.strip() for item in choices.split(";") if item.strip()]}
    )
    await update.message.reply_text(f"Q&A saved. ID: {record['id']}")


def register_admin_handlers(app: Application) -> None:
    app.add_handler(upload_conversation())
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(admin_menu, pattern=r"^admin:menu$"))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern=r"^admin:stats$"))
    app.add_handler(CallbackQueryHandler(admin_feedback, pattern=r"^admin:feedback$"))
    app.add_handler(CallbackQueryHandler(admin_results_help, pattern=r"^admin:results_help$"))
    app.add_handler(CallbackQueryHandler(admin_qa_help, pattern=r"^admin:qa_help$"))
    app.add_handler(CallbackQueryHandler(admin_delete_help, pattern=r"^admin:delete_help$"))
    app.add_handler(CommandHandler("delete_feedback", delete_feedback))
    app.add_handler(CommandHandler("delete_content", delete_content))
    app.add_handler(CommandHandler("set_result", set_result))
    app.add_handler(CommandHandler("add_qa", add_qa))
