from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from database.factory import content_repo, platform_repo
from keyboards.common import rows_from
from utils.i18n import BTN_BACK


async def qa_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❓ S&J Muraajaco\n\nXulo fasalka:", reply_markup=rows_from("qa:grade", platform_repo(context).get()["qa_classes"]))


async def qa_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    grade = query.data.split(":", 2)[2]
    context.user_data["qa_grade"] = grade
    level = platform_repo(context).level_for_class(grade)
    await query.edit_message_text("❓ S&J\n\nXulo maaddo:", reply_markup=rows_from("qa:subject", platform_repo(context).subjects_for_level(level), back="home:qa"))


async def qa_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    subject = query.data.split(":", 2)[2]
    items = content_repo(context, "qa").filter(grade=context.user_data["qa_grade"], subject=subject)
    if not items:
        await query.edit_message_text("📭 Su'aalo lama helin.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(BTN_BACK, callback_data="home:qa")]]))
        return
    rows = [[InlineKeyboardButton(f"❓ Su'aal {index + 1}", callback_data=f"qa:open:{item['id']}")] for index, item in enumerate(items[:10])]
    rows.append([InlineKeyboardButton(BTN_BACK, callback_data="home:qa")])
    await query.edit_message_text("❓ Xulo su'aal:", reply_markup=InlineKeyboardMarkup(rows))


async def qa_open(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    item_id = query.data.split(":")[-1]
    item = next((record for record in content_repo(context, "qa").all() if record["id"] == item_id), None)
    if not item:
        return
    choices = "\n".join(f"{idx + 1}. {choice}" for idx, choice in enumerate(item.get("choices", [])))
    await query.edit_message_text(f"❓ {item['question']}\n\n{choices}\n\n✅ Jawaab: {item['answer']}")


def register_qa_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(qa_entry, pattern=r"^home:qa$"))
    app.add_handler(CallbackQueryHandler(qa_grade, pattern=r"^qa:grade:"))
    app.add_handler(CallbackQueryHandler(qa_subject, pattern=r"^qa:subject:"))
    app.add_handler(CallbackQueryHandler(qa_open, pattern=r"^qa:open:"))
