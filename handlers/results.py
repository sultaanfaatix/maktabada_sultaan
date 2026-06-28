from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from database.factory import results_repo
from keyboards.common import rows_from
from utils.constants import RESULT_GRADES


async def results_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Send /result STUDENT_ID to view results.\nExample: /result F4-001")


async def result_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /result STUDENT_ID")
        return
    student = results_repo(context).get_student(context.args[0])
    if not student:
        await update.message.reply_text("No results found for that student ID.")
        return
    context.user_data["student_result"] = student["student_id"]
    grades = [grade for grade in RESULT_GRADES if grade in student.get("grades", {})]
    await update.message.reply_text("Choose grade.", reply_markup=rows_from("result:grade", grades or RESULT_GRADES, back="home:menu"))


async def result_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    grade = query.data.split(":", 2)[2]
    student = results_repo(context).get_student(context.user_data["student_result"])
    grade_data = student.get("grades", {}).get(grade, {})
    if not grade_data:
        await query.edit_message_text("No results for this grade.")
        return
    lines = [f"{student.get('name', student['student_id'])} - {grade}"]
    for exam_type, subjects in grade_data.items():
        total = sum(float(item["score"]) for item in subjects.values())
        max_total = sum(float(item["max_score"]) for item in subjects.values())
        lines.append(f"\n{exam_type}: {total:g}/{max_total:g}")
        for subject, item in subjects.items():
            lines.append(f"- {subject}: {item['score']:g}/{item['max_score']:g}")
    await query.edit_message_text("\n".join(lines))


def register_results_handlers(app: Application) -> None:
    app.add_handler(CallbackQueryHandler(results_entry, pattern=r"^home:results$"))
    app.add_handler(CommandHandler("result", result_lookup))
    app.add_handler(CallbackQueryHandler(result_grade, pattern=r"^result:grade:"))
