from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from utils.i18n import (
    BTN_ADMIN,
    BTN_ABOUT,
    BTN_BACK,
    BTN_BOOKS,
    BTN_EXAMS,
    BTN_FEEDBACK,
    BTN_LESSONS,
    BTN_PROFILE,
    BTN_QA,
    BTN_RESULTS,
    BTN_SETTINGS,
)


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(BTN_BOOKS, callback_data="home:books"), InlineKeyboardButton(BTN_EXAMS, callback_data="home:exams")],
        [InlineKeyboardButton(BTN_LESSONS, callback_data="home:lessons"), InlineKeyboardButton(BTN_RESULTS, callback_data="home:results")],
        [InlineKeyboardButton(BTN_QA, callback_data="home:qa"), InlineKeyboardButton(BTN_FEEDBACK, callback_data="home:feedback")],
        [InlineKeyboardButton(BTN_ABOUT, callback_data="about:home"), InlineKeyboardButton(BTN_PROFILE, callback_data="home:profile")],
        [InlineKeyboardButton(BTN_SETTINGS, callback_data="home:settings")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(BTN_ADMIN, callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)


def rows_from(prefix: str, values: list[str], columns: int = 2, back: str | None = "home:menu") -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for index in range(0, len(values), columns):
        rows.append([InlineKeyboardButton(value, callback_data=f"{prefix}:{value}") for value in values[index : index + columns]])
    if back:
        rows.append([InlineKeyboardButton(BTN_BACK, callback_data=back)])
    return InlineKeyboardMarkup(rows)


def content_list(prefix: str, items: list[dict], back: str, page: int = 0, page_size: int = 8) -> InlineKeyboardMarkup:
    start = page * page_size
    visible = items[start : start + page_size]
    rows = [[InlineKeyboardButton(f"📄 {item.get('title', item['id'])[:54]}", callback_data=f"{prefix}:open:{item['id']}")] for item in visible]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Hore", callback_data=f"{prefix}:page:{page - 1}"))
    if start + page_size < len(items):
        nav.append(InlineKeyboardButton("➡️ Xiga", callback_data=f"{prefix}:page:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(BTN_BACK, callback_data=back)])
    return InlineKeyboardMarkup(rows)


def bottom_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(BTN_BOOKS), KeyboardButton(BTN_EXAMS), KeyboardButton(BTN_LESSONS)],
        [KeyboardButton(BTN_RESULTS), KeyboardButton(BTN_QA), KeyboardButton(BTN_FEEDBACK)],
        [KeyboardButton(BTN_PROFILE), KeyboardButton(BTN_ABOUT), KeyboardButton(BTN_SETTINGS)],
    ]
    if is_admin:
        rows.append([KeyboardButton(BTN_ADMIN)])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)
