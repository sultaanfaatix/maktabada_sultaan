from __future__ import annotations

from telegram.ext import ContextTypes

from database.json_storage import JsonStorage
from database.repositories import (
    ActivityLogRepository,
    AdminRepository,
    AnalyticsRepository,
    AboutRepository,
    BackupRepository,
    ContentRepository,
    FeedbackRepository,
    PlatformSettingsRepository,
    ResultsRepository,
    StatsRepository,
)


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


def platform_repo(context: ContextTypes.DEFAULT_TYPE) -> PlatformSettingsRepository:
    return PlatformSettingsRepository(storage_from_context(context))


def admin_repo(context: ContextTypes.DEFAULT_TYPE) -> AdminRepository:
    return AdminRepository(storage_from_context(context), context.bot_data["settings"].admin_id)


def analytics_repo(context: ContextTypes.DEFAULT_TYPE) -> AnalyticsRepository:
    return AnalyticsRepository(storage_from_context(context))


def activity_repo(context: ContextTypes.DEFAULT_TYPE) -> ActivityLogRepository:
    return ActivityLogRepository(storage_from_context(context))


def backup_repo(context: ContextTypes.DEFAULT_TYPE) -> BackupRepository:
    return BackupRepository(storage_from_context(context))


def about_repo(context: ContextTypes.DEFAULT_TYPE) -> AboutRepository:
    return AboutRepository(storage_from_context(context))
