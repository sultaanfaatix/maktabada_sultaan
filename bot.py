from __future__ import annotations

import logging
import os
from pathlib import Path

from telegram.ext import Application, CommandHandler

from admin.panel import register_admin_handlers
from admin.analytics import register_analytics_handlers
from config import Settings
from handlers.books import register_books_handlers
from handlers.exams import register_exams_handlers
from handlers.feedback import register_feedback_handlers
from handlers.about import register_about_handlers
from handlers.lessons import register_lessons_handlers
from handlers.qa import register_qa_handlers
from handlers.results import register_results_handlers
from handlers.start import register_start_handlers

# =========================
# Data directory (Render Disk)
# =========================
DATA_DIR = Path("/data")
DATA_DIR.mkdir(exist_ok=True)

print("DATA DIR:", DATA_DIR)
print("Exists:", DATA_DIR.exists())


async def cancel(update, context) -> None:
    context.user_data.clear()
    await update.effective_message.reply_text("Operation cancelled.")


def build_application() -> Application:
    settings = Settings.from_env()
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )

    app = Application.builder().token(settings.bot_token).build()
    app.bot_data["settings"] = settings

    register_start_handlers(app)
    register_books_handlers(app)
    register_exams_handlers(app)
    register_lessons_handlers(app)
    register_results_handlers(app)
    register_qa_handlers(app)
    register_feedback_handlers(app)
    register_about_handlers(app)
    register_analytics_handlers(app)
    register_admin_handlers(app)

    app.add_handler(CommandHandler("cancel", cancel))
    return app


def main() -> None:
    application = build_application()
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()