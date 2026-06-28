from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("Books", callback_data="home:books"), InlineKeyboardButton("Exams", callback_data="home:exams")],
        [InlineKeyboardButton("Lessons", callback_data="home:lessons"), InlineKeyboardButton("Results", callback_data="home:results")],
        [InlineKeyboardButton("Q&A Revision", callback_data="home:qa"), InlineKeyboardButton("Feedback", callback_data="home:feedback")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton("Admin Panel", callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)


def rows_from(prefix: str, values: list[str], columns: int = 2, back: str | None = "home:menu") -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for index in range(0, len(values), columns):
        rows.append([InlineKeyboardButton(value, callback_data=f"{prefix}:{value}") for value in values[index : index + columns]])
    if back:
        rows.append([InlineKeyboardButton("Back", callback_data=back)])
    return InlineKeyboardMarkup(rows)


def content_list(prefix: str, items: list[dict], back: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(item.get("title", item["id"])[:60], callback_data=f"{prefix}:open:{item['id']}")] for item in items[:10]]
    rows.append([InlineKeyboardButton("Back", callback_data=back)])
    return InlineKeyboardMarkup(rows)
