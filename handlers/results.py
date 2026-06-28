from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from database.factory import platform_repo, results_repo
from keyboards.common import rows_from


def _aliases(grade: str) -> set[str]:
    if grade.endswith("aad") and grade[:-3].isdigit():
        return {grade, grade[:-3]}
    if grade.isdigit():
        return {grade, f"{grade}aad"}
    return {grade}


async def results_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📊 Natiijooyin\n\nSoo dir: /result STUDENT_ID\nTusaale: /result F4-001")


async def result_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Isticmaal: /result STUDENT_ID")
        return
    student = results_repo(context).get_student(context.args[0])
    if not student:
        await update.message.reply_text("Natiijo lagama helin Student ID-gaas.")
        return
    context.user_data["student_result"] = student["student_id"]
    configured = platform_repo(context).get()["result_classes"]
    stored = student.get("grades", {})
    grades = [grade for grade in configured if any(alias in stored for alias in _aliases(grade))]
    await update.message.reply_text("📊 Xulo fasalka:", reply_markup=rows_from("result:grade", grades or configured, back="home:menu"))


async def result_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    grade = query.data.split(":", 2)[2]
    student = results_repo(context).get_student(context.user_data["student_result"])
    stored = student.get("grades", {})
    grade_data = next((stored[alias] for alias in _aliases(grade) if alias in stored), {})
    if not grade_data:
        await query.edit_message_text("Natiijo fasalkan lagama helin.")
        return
    lines = [f"📊 {student.get('name', student['student_id'])} - {grade}"]
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
