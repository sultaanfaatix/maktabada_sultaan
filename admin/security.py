from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable

from telegram import Update
from telegram.ext import ContextTypes

from database.factory import admin_repo


def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return bool(update.effective_user and admin_repo(context).is_admin(update.effective_user.id))


def has_permission(update: Update, context: ContextTypes.DEFAULT_TYPE, permission: str) -> bool:
    return bool(update.effective_user and admin_repo(context).has_permission(update.effective_user.id, permission))


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


def require_permission(permission: str) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
            if not has_permission(update, context, permission):
                message = update.effective_message
                query = update.callback_query
                if query:
                    await query.answer("Ogolaansho kuma filna.", show_alert=True)
                elif message:
                    await message.reply_text("Ogolaansho kuma filna.")
                return None
            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator
