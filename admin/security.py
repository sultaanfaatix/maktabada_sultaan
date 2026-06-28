from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable

from telegram import Update
from telegram.ext import ContextTypes


def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return bool(update.effective_user and update.effective_user.id == context.bot_data["settings"].admin_id)


def admin_only(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        if not is_admin(update, context):
            message = update.effective_message
            query = update.callback_query
            if query:
                await query.answer("Admin only.", show_alert=True)
            elif message:
                await message.reply_text("Admin only.")
            return None
        return await func(update, context, *args, **kwargs)

    return wrapper
