from __future__ import annotations

from telegram.ext import ContextTypes

from database.json_storage import JsonStorage
from database.repositories import ContentRepository, FeedbackRepository, ResultsRepository, StatsRepository


def storage_from_context(context: ContextTypes.DEFAULT_TYPE) -> JsonStorage:
    return JsonStorage(context.bot_data["settings"].data_dir)


def content_repo(context: ContextTypes.DEFAULT_TYPE, collection: str) -> ContentRepository:
    return ContentRepository(storage_from_context(context), collection)


def feedback_repo(context: ContextTypes.DEFAULT_TYPE) -> FeedbackRepository:
    return FeedbackRepository(storage_from_context(context))


def results_repo(context: ContextTypes.DEFAULT_TYPE) -> ResultsRepository:
    return ResultsRepository(storage_from_context(context))


def stats_repo(context: ContextTypes.DEFAULT_TYPE) -> StatsRepository:
    return StatsRepository(storage_from_context(context))
