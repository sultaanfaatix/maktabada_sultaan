from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from admin.security import admin_only, require_permission
from admin.uploads import upload_conversation
from database.factory import activity_repo, admin_repo, backup_repo, content_repo, feedback_repo, platform_repo, results_repo, stats_repo
from utils.i18n import ALL_PERMISSIONS, PERMISSION_LABELS


def admin_menu_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📚 Upload Buug", callback_data="admin:upload:books")],
            [InlineKeyboardButton("📝 Upload Imtixaan", callback_data="admin:upload:exams")],
            [InlineKeyboardButton("🎓 Upload Cashar", callback_data="admin:upload:lessons")],
            [InlineKeyboardButton("📊 Natiijooyin", callback_data="admin:results_help"), InlineKeyboardButton("❓ S&J", callback_data="admin:qa_help")],
            [InlineKeyboardButton("📖 Maaddooyin", callback_data="admin:subjects_help"), InlineKeyboardButton("🏫 Fasallo", callback_data="admin:classes_help")],
            [InlineKeyboardButton("📅 Sanad Dugsiyeed", callback_data="admin:years_help"), InlineKeyboardButton("👥 Admins", callback_data="admin:admins_help")],
            [InlineKeyboardButton("📈 Statistics", callback_data="admin:stats"), InlineKeyboardButton("💬 Faallo", callback_data="admin:feedback")],
            [InlineKeyboardButton("🗂 Files", callback_data="admin:files_help"), InlineKeyboardButton("💾 Backup", callback_data="admin:backup_help")],
            [InlineKeyboardButton("🔙 Dib-u-noqo", callback_data="home:menu")],
        ]
    )


@admin_only
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("⚙️ Maamulka", reply_markup=admin_menu_markup())


@admin_only
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚙️ Maamulka", reply_markup=admin_menu_markup())


@require_permission("view_statistics")
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    stats = stats_repo(context).snapshot()
    text = "\n".join(f"{key.replace('_', ' ').title()}: {value}" for key, value in stats.items())
    await query.edit_message_text(f"📈 Statistics\n\n{text}", reply_markup=admin_menu_markup())


@admin_only
async def admin_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    items = feedback_repo(context).all()[-10:]
    if not items:
        await query.edit_message_text("💬 Weli faallo ma jirto.", reply_markup=admin_menu_markup())
        return
    text = "\n\n".join(f"{item['id']} | {item['name']}\n{item['comment']}" for item in items)
    await query.edit_message_text(f"💬 Faallooyinkii ugu dambeeyay:\n\n{text}\n\nTirtir: /delete_feedback ID", reply_markup=admin_menu_markup())


@require_permission("manage_results")
async def admin_results_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📊 Maamul Natiijooyin\n\n"
        "/set_result STUDENT_ID | Name | Grade | Exam Type | Subject | Score | Max\n\n"
        "Tusaale:\n/set_result F4-001 | Ahmed Ali | Form 4 | Final Exam | Mathematics | 92 | 100",
        reply_markup=admin_menu_markup(),
    )


@admin_only
async def admin_qa_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "❓ Maamul S&J\n\n"
        "/add_qa Grade | Subject | Question | Answer | choice A ; choice B ; choice C",
        reply_markup=admin_menu_markup(),
    )


@require_permission("manage_subjects")
async def admin_subjects_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📖 Maamul Maaddooyin\n\n"
        "/add_subject primary|middle|secondary | Maaddo\n"
        "/rename_subject level | Old | New\n"
        "/delete_subject level | Maaddo",
        reply_markup=admin_menu_markup(),
    )


@require_permission("manage_classes")
async def admin_classes_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏫 Maamul Fasallo\n\n"
        "/add_class primary|middle|secondary | Fasal\n"
        "/rename_class level | Old | New\n"
        "/delete_class level | Fasal",
        reply_markup=admin_menu_markup(),
    )


@require_permission("manage_years")
async def admin_years_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📅 Maamul Sanad Dugsiyeed\n\n"
        "/add_year 2026-2027\n"
        "/rename_year 2025-2026 | 2025/2026\n"
        "/delete_year 2016-2017",
        reply_markup=admin_menu_markup(),
    )


@require_permission("manage_admins")
async def admin_admins_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    permissions = "\n".join(f"- {key}: {label}" for key, label in PERMISSION_LABELS.items())
    await query.edit_message_text(
        "👥 Multi-Admin\n\n"
        "/add_admin USER_ID | full\n"
        "/add_admin USER_ID | upload_books,manage_results\n"
        "/remove_admin USER_ID\n"
        "/list_admins\n\n"
        f"Permissions:\n{permissions}",
        reply_markup=admin_menu_markup(),
    )


@admin_only
async def admin_files_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🗂 File Management\n\n"
        "/rename_file books|exams|lessons ID | New Title\n"
        "/delete_content books|exams|lessons|qa ID\n\n"
        "Replace file: upload a new item, then delete the old ID.",
        reply_markup=admin_menu_markup(),
    )


@require_permission("backup_restore")
async def admin_backup_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💾 Backup\n\n/create_backup wuxuu abuurayaa backup JSON ah.", reply_markup=admin_menu_markup())


@admin_only
async def delete_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Isticmaal: /delete_feedback FEEDBACK_ID")
        return
    deleted = feedback_repo(context).delete(context.args[0])
    activity_repo(context).log(update.effective_user.id, "delete_feedback", {"id": context.args[0]})
    await update.message.reply_text("Faallo waa la tirtiray." if deleted else "Faallo lama helin.")


@require_permission("delete_content")
async def delete_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2 or context.args[0] not in {"books", "exams", "lessons", "qa"}:
        await update.message.reply_text("Isticmaal: /delete_content books|exams|lessons|qa CONTENT_ID")
        return
    deleted = content_repo(context, context.args[0]).delete(context.args[1])
    activity_repo(context).log(update.effective_user.id, "delete_content", {"collection": context.args[0], "id": context.args[1]})
    await update.message.reply_text("Content waa la tirtiray." if deleted else "Content lama helin.")


@require_permission("delete_content")
async def rename_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw = update.message.text.removeprefix("/rename_file").strip()
    if "|" not in raw:
        await update.message.reply_text("Isticmaal: /rename_file books|exams|lessons ID | New Title")
        return
    left, title = [part.strip() for part in raw.split("|", 1)]
    parts = left.split()
    if len(parts) != 2 or parts[0] not in {"books", "exams", "lessons"}:
        await update.message.reply_text("Isticmaal: /rename_file books|exams|lessons ID | New Title")
        return
    updated = content_repo(context, parts[0]).update(parts[1], {"title": title})
    await update.message.reply_text("Magaca waa la beddelay." if updated else "File lama helin.")


@require_permission("manage_results")
async def set_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw = update.message.text.removeprefix("/set_result").strip()
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) != 7:
        await update.message.reply_text("Isticmaal: /set_result STUDENT_ID | Name | Grade | Exam Type | Subject | Score | Max")
        return
    sid, name, grade, exam_type, subject, score, max_score = parts
    try:
        score_value = float(score)
        max_value = float(max_score)
    except ValueError:
        await update.message.reply_text("Score iyo Max waa inay noqdaan tiro.")
        return
    results_repo(context).upsert_score(sid, name, grade, exam_type, subject, score_value, max_value)
    activity_repo(context).log(update.effective_user.id, "set_result", {"student_id": sid, "grade": grade})
    await update.message.reply_text("Natiijada waa la keydiyay.")


@admin_only
async def add_qa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw = update.message.text.removeprefix("/add_qa").strip()
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) < 5:
        await update.message.reply_text("Isticmaal: /add_qa Grade | Subject | Question | Answer | choice A ; choice B ; choice C")
        return
    grade, subject, question, answer, choices = parts[:5]
    record = content_repo(context, "qa").add(
        {"grade": grade, "subject": subject, "question": question, "answer": answer, "choices": [item.strip() for item in choices.split(";") if item.strip()]}
    )
    activity_repo(context).log(update.effective_user.id, "add_qa", {"id": record["id"]})
    await update.message.reply_text(f"S&J waa la keydiyay. ID: {record['id']}")


@require_permission("manage_subjects")
async def add_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts = [part.strip() for part in update.message.text.removeprefix("/add_subject").split("|")]
    if len(parts) != 2:
        await update.message.reply_text("Isticmaal: /add_subject primary|middle|secondary | Maaddo")
        return
    platform_repo(context).add_subject(parts[0], parts[1])
    await update.message.reply_text("Maaddada waa la daray.")


@require_permission("manage_subjects")
async def rename_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts = [part.strip() for part in update.message.text.removeprefix("/rename_subject").split("|")]
    if len(parts) != 3:
        await update.message.reply_text("Isticmaal: /rename_subject level | Old | New")
        return
    await update.message.reply_text("Maaddada waa la beddelay." if platform_repo(context).rename_subject(parts[0], parts[1], parts[2]) else "Maaddada lama helin.")


@require_permission("manage_subjects")
async def delete_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts = [part.strip() for part in update.message.text.removeprefix("/delete_subject").split("|")]
    if len(parts) != 2:
        await update.message.reply_text("Isticmaal: /delete_subject level | Maaddo")
        return
    await update.message.reply_text("Maaddada waa la tirtiray." if platform_repo(context).delete_subject(parts[0], parts[1]) else "Maaddada lama helin.")


@require_permission("manage_classes")
async def add_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts = [part.strip() for part in update.message.text.removeprefix("/add_class").split("|")]
    if len(parts) != 2:
        await update.message.reply_text("Isticmaal: /add_class primary|middle|secondary | Fasal")
        return
    platform_repo(context).add_class(parts[0], parts[1])
    await update.message.reply_text("Fasalka waa la daray.")


@require_permission("manage_classes")
async def rename_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts = [part.strip() for part in update.message.text.removeprefix("/rename_class").split("|")]
    if len(parts) != 3:
        await update.message.reply_text("Isticmaal: /rename_class level | Old | New")
        return
    await update.message.reply_text("Fasalka waa la beddelay." if platform_repo(context).rename_class(parts[0], parts[1], parts[2]) else "Fasalka lama helin.")


@require_permission("manage_classes")
async def delete_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts = [part.strip() for part in update.message.text.removeprefix("/delete_class").split("|")]
    if len(parts) != 2:
        await update.message.reply_text("Isticmaal: /delete_class level | Fasal")
        return
    await update.message.reply_text("Fasalka waa la tirtiray." if platform_repo(context).delete_class(parts[0], parts[1]) else "Fasalka lama helin.")


@require_permission("manage_years")
async def add_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    year = " ".join(context.args).strip()
    if not year:
        await update.message.reply_text("Isticmaal: /add_year 2026-2027")
        return
    platform_repo(context).add_year(year)
    await update.message.reply_text("Sanad dugsiyeedka waa la daray.")


@require_permission("manage_years")
async def rename_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts = [part.strip() for part in update.message.text.removeprefix("/rename_year").split("|")]
    if len(parts) != 2:
        await update.message.reply_text("Isticmaal: /rename_year Old | New")
        return
    await update.message.reply_text("Sanadka waa la beddelay." if platform_repo(context).rename_year(parts[0], parts[1]) else "Sanadka lama helin.")


@require_permission("manage_years")
async def delete_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    year = " ".join(context.args).strip()
    if not year:
        await update.message.reply_text("Isticmaal: /delete_year 2016-2017")
        return
    await update.message.reply_text("Sanadka waa la tirtiray." if platform_repo(context).delete_year(year) else "Sanadka lama helin.")


@require_permission("manage_admins")
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    raw = update.message.text.removeprefix("/add_admin").strip()
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) != 2 or not parts[0].isdigit():
        await update.message.reply_text("Isticmaal: /add_admin USER_ID | full ama permission1,permission2")
        return
    permissions = ALL_PERMISSIONS if parts[1].casefold() == "full" else [p.strip() for p in parts[1].split(",")]
    admin_repo(context).add(int(parts[0]), permissions)
    await update.message.reply_text("Admin waa la daray.")


@require_permission("manage_admins")
async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Isticmaal: /remove_admin USER_ID")
        return
    await update.message.reply_text("Admin waa la saaray." if admin_repo(context).remove(int(context.args[0])) else "Admin lama saari karin.")


@require_permission("manage_admins")
async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = []
    for admin in admin_repo(context).all().values():
        lines.append(f"{admin['user_id']} | {admin.get('role', 'custom')} | {', '.join(admin.get('permissions', []))}")
    await update.message.reply_text("👥 Admins:\n\n" + "\n".join(lines))


@require_permission("backup_restore")
async def create_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    path = backup_repo(context).create()
    await update.message.reply_text(f"Backup waa la sameeyay:\n{path}")


def register_admin_handlers(app: Application) -> None:
    app.add_handler(upload_conversation())
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(admin_menu, pattern=r"^admin:menu$"))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern=r"^admin:stats$"))
    app.add_handler(CallbackQueryHandler(admin_feedback, pattern=r"^admin:feedback$"))
    app.add_handler(CallbackQueryHandler(admin_results_help, pattern=r"^admin:results_help$"))
    app.add_handler(CallbackQueryHandler(admin_qa_help, pattern=r"^admin:qa_help$"))
    app.add_handler(CallbackQueryHandler(admin_subjects_help, pattern=r"^admin:subjects_help$"))
    app.add_handler(CallbackQueryHandler(admin_classes_help, pattern=r"^admin:classes_help$"))
    app.add_handler(CallbackQueryHandler(admin_years_help, pattern=r"^admin:years_help$"))
    app.add_handler(CallbackQueryHandler(admin_admins_help, pattern=r"^admin:admins_help$"))
    app.add_handler(CallbackQueryHandler(admin_files_help, pattern=r"^admin:files_help$"))
    app.add_handler(CallbackQueryHandler(admin_backup_help, pattern=r"^admin:backup_help$"))
    app.add_handler(CommandHandler("delete_feedback", delete_feedback))
    app.add_handler(CommandHandler("delete_content", delete_content))
    app.add_handler(CommandHandler("rename_file", rename_file))
    app.add_handler(CommandHandler("set_result", set_result))
    app.add_handler(CommandHandler("add_qa", add_qa))
    app.add_handler(CommandHandler("add_subject", add_subject))
    app.add_handler(CommandHandler("rename_subject", rename_subject))
    app.add_handler(CommandHandler("delete_subject", delete_subject))
    app.add_handler(CommandHandler("add_class", add_class))
    app.add_handler(CommandHandler("rename_class", rename_class))
    app.add_handler(CommandHandler("delete_class", delete_class))
    app.add_handler(CommandHandler("add_year", add_year))
    app.add_handler(CommandHandler("rename_year", rename_year))
    app.add_handler(CommandHandler("delete_year", delete_year))
    app.add_handler(CommandHandler("add_admin", add_admin))
    app.add_handler(CommandHandler("remove_admin", remove_admin))
    app.add_handler(CommandHandler("list_admins", list_admins))
    app.add_handler(CommandHandler("create_backup", create_backup))
