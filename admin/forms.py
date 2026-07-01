from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from admin.security import has_permission, require_permission
from database.factory import activity_repo, admin_repo, backup_repo, content_repo, platform_repo, results_repo
from utils.i18n import ALL_PERMISSIONS, PERMISSION_LABELS

FORM_TEXT = 910


def back_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Maamulka", callback_data="admin:menu")]])


def level_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Dugsi Hoose", callback_data=f"{prefix}:primary"), InlineKeyboardButton("Dugsi Dhexe", callback_data=f"{prefix}:middle")],
            [InlineKeyboardButton("Dugsi Sare", callback_data=f"{prefix}:secondary")],
            [InlineKeyboardButton("🔙 Maamulka", callback_data="admin:menu")],
        ]
    )


def action_keyboard(area: str, actions: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(label, callback_data=f"form:{area}:{action}")] for action, label in actions]
    rows.append([InlineKeyboardButton("🔙 Maamulka", callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)


async def subjects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not has_permission(update, context, "manage_subjects"):
        await query.answer("Ogolaansho lama bixin.", show_alert=True)
        return
    await query.edit_message_text(
        "📖 Maaddooyin\n\nDooro hawsha aad rabto:",
        reply_markup=action_keyboard("subject", [("add", "➕ Ku dar maaddo"), ("rename", "✏️ Bedel maaddo"), ("delete", "🗑 Tirtir maaddo")]),
    )


async def classes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not has_permission(update, context, "manage_classes"):
        await query.answer("Ogolaansho kuma filna.", show_alert=True)
        return
    await query.edit_message_text(
        "🏫 Fasallo\n\nDooro hawsha aad rabto:",
        reply_markup=action_keyboard("class", [("add", "➕ Ku dar fasal"), ("rename", "✏️ Bedel fasal"), ("delete", "🗑 Tirtir fasal")]),
    )


async def years_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not has_permission(update, context, "manage_years"):
        await query.answer("Ogolaansho lama bixin.", show_alert=True)
        return
    await query.edit_message_text(
        "📅 Sanad Dugsiyeed\n\nDooro hawsha aad rabto:",
        reply_markup=action_keyboard("year", [("add", "➕ Ku dar sanad dugsiyeed"), ("rename", "✏️ Beddel sanad"), ("delete", "🗑 Tirtir sanad")]),
    )


async def config_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, area, action = query.data.split(":")
    context.user_data["form"] = {"area": area, "action": action}
    if area in {"subject", "class"}:
        await query.edit_message_text("Xulo heerka:", reply_markup=level_keyboard(f"form:{area}:level"))
        return FORM_TEXT
    if area == "year" and action == "add":
        await query.edit_message_text("Qor sanad dugsiyeedka cusub. Tusaale: 2026-2027", reply_markup=back_admin())
        context.user_data["form"]["step"] = "year_new"
        return FORM_TEXT
    years = platform_repo(context).get()["exam_years"]
    rows = [[InlineKeyboardButton(year, callback_data=f"form:year:item:{year}")] for year in years]
    rows.append([InlineKeyboardButton("🔙 Maamulka", callback_data="admin:menu")])
    await query.edit_message_text("Xulo sanad:", reply_markup=InlineKeyboardMarkup(rows))
    return FORM_TEXT


async def config_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, area, _, level = query.data.split(":")
    form = context.user_data["form"]
    form["level"] = level
    repo = platform_repo(context)
    if form["action"] == "add":
        form["step"] = f"{area}_new"
        await query.edit_message_text("Qor magaca cusub:", reply_markup=back_admin())
        return FORM_TEXT
    values = repo.subjects_for_level(level) if area == "subject" else repo.classes_for_level(level)
    rows = [[InlineKeyboardButton(value, callback_data=f"form:{area}:item:{value}")] for value in values]
    rows.append([InlineKeyboardButton("🔙 Maamulka", callback_data="admin:menu")])
    await query.edit_message_text("Xulo item-ka:", reply_markup=InlineKeyboardMarkup(rows))
    return FORM_TEXT


async def config_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    _, area, _, value = query.data.split(":", 3)
    form = context.user_data["form"]
    form["old"] = value
    if form["action"] == "delete":
        ok = apply_config_change(context, form, None)
        await query.edit_message_text("✅ Waa la tirtiray." if ok else "Item lama helin.", reply_markup=back_admin())
        return ConversationHandler.END
    form["step"] = f"{area}_rename"
    await query.edit_message_text(f"Qor magaca cusub ee lagu beddelayo:\n{value}", reply_markup=back_admin())
    return FORM_TEXT


async def config_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    form = context.user_data.get("form", {})
    text = update.message.text.strip()
    ok = apply_config_change(context, form, text)
    activity_repo(context).log(update.effective_user.id, "interactive_config", form)
    await update.message.reply_text("✅ Waa la keydiyay." if ok else "⚠️ Lama dhammaystirin. Hubi xulashada.", reply_markup=back_admin())
    return ConversationHandler.END


def apply_config_change(context: ContextTypes.DEFAULT_TYPE, form: dict, text: str | None) -> bool:
    repo = platform_repo(context)
    area = form.get("area")
    action = form.get("action")
    level = form.get("level")
    if area == "subject":
        if action == "add" and text:
            repo.add_subject(level, text)
            return True
        if action == "rename" and text:
            return repo.rename_subject(level, form["old"], text)
        if action == "delete":
            return repo.delete_subject(level, form["old"])
    if area == "class":
        if action == "add" and text:
            repo.add_class(level, text)
            return True
        if action == "rename" and text:
            return repo.rename_class(level, form["old"], text)
        if action == "delete":
            return repo.delete_class(level, form["old"])
    if area == "year":
        if action == "add" and text:
            repo.add_year(text)
            return True
        if action == "rename" and text:
            return repo.rename_year(form["old"], text)
        if action == "delete":
            return repo.delete_year(form["old"])
    return False


async def year_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    year = query.data.split(":", 3)[3]
    form = context.user_data["form"]
    form["old"] = year
    if form["action"] == "delete":
        ok = apply_config_change(context, form, None)
        await query.edit_message_text("✅ Sanadka waa la tirtiray." if ok else "Sanad lama helin.", reply_markup=back_admin())
        return ConversationHandler.END
    await query.edit_message_text(f"Qor magaca cusub ee sanadkan:\n{year}", reply_markup=back_admin())
    return FORM_TEXT


@require_permission("manage_results")
async def result_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["result_form"] = {"step": "student_id"}
    await query.edit_message_text("📊 Natiijo Cusub\n\nQor Student ID:", reply_markup=back_admin())
    return FORM_TEXT


async def result_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    form = context.user_data["result_form"]
    text = update.message.text.strip()
    step = form["step"]
    if step == "student_id":
        form["student_id"] = text.upper()
        form["step"] = "name"
        await update.message.reply_text("Qor magaca ardayga:", reply_markup=back_admin())
    elif step == "name":
        form["name"] = text
        form["step"] = "score"
        await update.message.reply_text("Qor score iyo max sidan: 92/100", reply_markup=back_admin())
    elif step == "score":
        if "/" not in text:
            await update.message.reply_text("Fadlan qor sidan: 92/100")
            return FORM_TEXT
        score, max_score = [part.strip() for part in text.split("/", 1)]
        results_repo(context).upsert_score(form["student_id"], form["name"], form["grade"], form["exam_type"], form["subject"], float(score), float(max_score))
        activity_repo(context).log(update.effective_user.id, "interactive_result", form)
        await update.message.reply_text("✅ Natiijada waa la keydiyay.", reply_markup=back_admin())
        return ConversationHandler.END
    return FORM_TEXT


async def result_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    grade = query.data.split(":", 2)[2]
    context.user_data["result_form"]["grade"] = grade
    rows = [[InlineKeyboardButton(item, callback_data=f"form:result_exam:{item}")] for item in platform_repo(context).get()["exam_types"]]
    await query.edit_message_text("Xulo nooca imtixaanka:", reply_markup=InlineKeyboardMarkup(rows))
    return FORM_TEXT


async def result_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    exam_type = query.data.split(":", 2)[2]
    form = context.user_data["result_form"]
    form["exam_type"] = exam_type
    level = platform_repo(context).level_for_class(form["grade"])
    rows = [[InlineKeyboardButton(item, callback_data=f"form:result_subject:{item}")] for item in platform_repo(context).subjects_for_level(level)]
    await query.edit_message_text("Xulo maaddo:", reply_markup=InlineKeyboardMarkup(rows))
    return FORM_TEXT


async def result_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["result_form"]["subject"] = query.data.split(":", 2)[2]
    await query.edit_message_text("Qor score iyo max sidan: 92/100", reply_markup=back_admin())
    context.user_data["result_form"]["step"] = "score"
    return FORM_TEXT


@require_permission("manage_results")
async def result_pick_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    rows = [[InlineKeyboardButton(item, callback_data=f"form:result_grade:{item}")] for item in platform_repo(context).get()["result_classes"]]
    await query.edit_message_text("Xulo fasalka:", reply_markup=InlineKeyboardMarkup(rows))
    return FORM_TEXT


@require_permission("manage_admins")
async def admins_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👥 Admins\n\nDooro hawsha:",
        reply_markup=action_keyboard("admin", [("add", "➕ Ku dar admin"), ("remove", "🗑 Saar admin"), ("list", "📋 Liiska admins")]),
    )


async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[2]
    if action == "list":
        lines = [f"{a['user_id']} | {a.get('role')} | {', '.join(a.get('permissions', []))}" for a in admin_repo(context).all().values()]
        await query.edit_message_text("👥 Admins\n\n" + "\n".join(lines), reply_markup=back_admin())
        return ConversationHandler.END
    context.user_data["admin_form"] = {"action": action, "step": "user_id"}
    await query.edit_message_text("Qor Telegram User ID:", reply_markup=back_admin())
    return FORM_TEXT


async def admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    form = context.user_data["admin_form"]
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("User ID waa inuu tiro noqdaa.")
        return FORM_TEXT
    user_id = int(text)
    if form["action"] == "remove":
        ok = admin_repo(context).remove(user_id)
        await update.message.reply_text("✅ Admin waa la saaray." if ok else "Admin lama saari karin.", reply_markup=back_admin())
        return ConversationHandler.END
    form["user_id"] = user_id
    await update.message.reply_text(
        "Dooro permission type:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Full Admin", callback_data="form:admin_perm:full")],
                [InlineKeyboardButton("Custom Permissions", callback_data="form:admin_perm:custom")],
            ]
        ),
    )
    return FORM_TEXT


async def admin_perm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    mode = query.data.split(":")[-1]
    form = context.user_data["admin_form"]
    if mode == "full":
        admin_repo(context).add(form["user_id"], ALL_PERMISSIONS)
        await query.edit_message_text("✅ Full admin waa la daray.", reply_markup=back_admin())
        return ConversationHandler.END
    form["permissions"] = []
    await query.edit_message_text("Dooro permissions, kadib Save:", reply_markup=permissions_keyboard([]))
    return FORM_TEXT


def permissions_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for key, label in PERMISSION_LABELS.items():
        mark = "☑" if key in selected else "☐"
        rows.append([InlineKeyboardButton(f"{mark} {label}", callback_data=f"form:perm_toggle:{key}")])
    rows.append([InlineKeyboardButton("✅ Save", callback_data="form:perm_save")])
    return InlineKeyboardMarkup(rows)


async def perm_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    key = query.data.split(":")[-1]
    selected = context.user_data["admin_form"]["permissions"]
    if key in selected:
        selected.remove(key)
    else:
        selected.append(key)
    await query.edit_message_text("Dooro permissions, kadib Save:", reply_markup=permissions_keyboard(selected))
    return FORM_TEXT


async def perm_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    form = context.user_data["admin_form"]
    admin_repo(context).add(form["user_id"], form["permissions"])
    await query.edit_message_text("✅ Custom admin waa la daray.", reply_markup=back_admin())
    return ConversationHandler.END


async def cancel_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    for key in ["form", "result_form", "admin_form"]:
        context.user_data.pop(key, None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Form waa la xiray.", reply_markup=back_admin())
    else:
        await update.effective_message.reply_text("Form waa la xiray.", reply_markup=back_admin())
    return ConversationHandler.END


def admin_forms_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(config_action, pattern=r"^form:(subject|class|year):(add|rename|delete)$"),
            CallbackQueryHandler(result_start, pattern=r"^form:result:start$"),
            CallbackQueryHandler(result_pick_grade, pattern=r"^form:result:grade_start$"),
            CallbackQueryHandler(admin_action, pattern=r"^form:admin:(add|remove|list)$"),
        ],
        states={
            FORM_TEXT: [
                CallbackQueryHandler(config_level, pattern=r"^form:(subject|class):level:"),
                CallbackQueryHandler(config_item, pattern=r"^form:(subject|class):item:"),
                CallbackQueryHandler(year_item, pattern=r"^form:year:item:"),
                CallbackQueryHandler(result_grade, pattern=r"^form:result_grade:"),
                CallbackQueryHandler(result_exam, pattern=r"^form:result_exam:"),
                CallbackQueryHandler(result_subject, pattern=r"^form:result_subject:"),
                CallbackQueryHandler(admin_perm, pattern=r"^form:admin_perm:"),
                CallbackQueryHandler(perm_toggle, pattern=r"^form:perm_toggle:"),
                CallbackQueryHandler(perm_save, pattern=r"^form:perm_save$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, route_text),
            ]
        },
        fallbacks=[CallbackQueryHandler(cancel_form, pattern=r"^admin:menu$")],
        per_message=False,
    )


async def route_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "result_form" in context.user_data:
        return await result_text(update, context)
    if "admin_form" in context.user_data:
        return await admin_text(update, context)
    return await config_text(update, context)


def register_admin_form_handlers(app: Application) -> None:
    app.add_handler(admin_forms_conversation())
    app.add_handler(CallbackQueryHandler(subjects_menu, pattern=r"^admin:subjects$"))
    app.add_handler(CallbackQueryHandler(classes_menu, pattern=r"^admin:classes$"))
    app.add_handler(CallbackQueryHandler(years_menu, pattern=r"^admin:years$"))
    app.add_handler(CallbackQueryHandler(admins_menu, pattern=r"^admin:admins$"))
