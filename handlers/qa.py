from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from database.factory import content_repo
from keyboards.common import rows_from
from utils.constants import BOOK_LEVELS, QA_GRADES


async def qa_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Q&A Revision: choose grade.", reply_markup=rows_from("qa:grade", QA_GRADES))


async def qa_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    grade = query.data.split(":", 2)[2]
    context.user_data["qa_grade"] = grade
    subjects = BOOK_LEVELS["secondary"]["subjects"] if "Form" in grade else BOOK_LEVELS["middle"]["subjects"]
    await query.edit_message_text("Choose subject.", reply_markup=rows_from("qa:subject", subjects, back="home:qa"))


async def qa_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    subject = query.data.split(":", 2)[2]
    items = content_repo(context, "qa").filter(grade=context.user_data["qa_grade"], subject=subject)
    if not items:
        await query.edit_message_text("No questions found.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home:qa")]]))
        return
    rows = [[InlineKeyboardButton(f"Question {index + 1}", callback_data=f"qa:open:{item['id']}")] for index, item in enumerate(items[:10])]
    rows.append([InlineKeyboardButton("Back", callback_data="home:qa")])
    await query.edit_message_text("Choose a question.", reply_markup=InlineKeyboardMarkup(rows))


async def qa_open(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    item_id = query.data.split(":")[-1]
    item = next((record for record in content_repo(context, "qa").all() if record["id"] == item_id), None)
    if not item:
        return
    choices = "\n".join(f"{idx + 1}. {choice}" for idx, choice in enumerate(item.get("choices", [])))
    await query.edit_message_text(f"{item['question']}\n\n{choices}\n\nAnswer: {item['answer']}")


def register_qa_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(qa_entry, pattern=r"^home:qa$"))
    app.add_handler(CallbackQueryHandler(qa_grade, pattern=r"^qa:grade:"))
    app.add_handler(CallbackQueryHandler(qa_subject, pattern=r"^qa:subject:"))
    app.add_handler(CallbackQueryHandler(qa_open, pattern=r"^qa:open:"))
