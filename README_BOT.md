# MAKTABADA SULTAAN v2

Modern Somali-localized Telegram education bot built with Python and `python-telegram-bot`.

## Highlights

- 📚 Buugaag: class, subject, book type, Telegram PDF `file_id`, search
- 📝 Imtixaanaad: 8aad and Form 4, years 2016-2017 to 2025-2026
- 🎓 Casharro: Form 1 to Form 4, PDF or video lessons
- 📊 Natiijooyin: student ID lookup and grade results
- ❓ S&J Muraajaco: MCQ or text revision questions
- 💬 Faallo: feedback stored in JSON
- ⚙️ Maamulka: multi-admin, permissions, uploads, stats, settings, backups
- Persistent Telegram bottom menu plus clean inline navigation

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create or edit `.env`:

```env
BOT_TOKEN=your-bot-token
ADMIN_ID=your-telegram-user-id
DATA_DIR=database/json_data
```

Run:

```powershell
python bot.py
```

## Multi-Admin

Owner admin is always the `ADMIN_ID` from `.env`.

Commands:

- `/add_admin USER_ID | full`
- `/add_admin USER_ID | upload_books,manage_results`
- `/remove_admin USER_ID`
- `/list_admins`

Permissions:

- `upload_books`
- `upload_exams`
- `upload_lessons`
- `manage_results`
- `manage_subjects`
- `manage_classes`
- `manage_years`
- `manage_admins`
- `view_statistics`
- `delete_content`
- `backup_restore`

## Dynamic Settings

- `/add_subject primary|middle|secondary | Maaddo`
- `/rename_subject level | Old | New`
- `/delete_subject level | Maaddo`
- `/add_class primary|middle|secondary | Fasal`
- `/rename_class level | Old | New`
- `/delete_class level | Fasal`
- `/add_year 2026-2027`
- `/rename_year Old | New`
- `/delete_year 2016-2017`

Defaults:

- `Cilmi Bulsho` is included in `Dugsi Hoose` and `Dugsi Dhexe`.
- `5aad` is removed from `Dugsi Hoose`.
- Exam years include `2016-2017`, `2017-2018`, and `2018-2019`.

## Admin Content Commands

- `/admin`
- `/set_result STUDENT_ID | Name | Grade | Exam Type | Subject | Score | Max`
- `/add_qa Grade | Subject | Question | Answer | choice A ; choice B ; choice C`
- `/rename_file books|exams|lessons ID | New Title`
- `/delete_content books|exams|lessons|qa CONTENT_ID`
- `/delete_feedback FEEDBACK_ID`
- `/create_backup`

Uploads are guided from the inline admin panel and store Telegram `file_id` values in JSON.

## Architecture

```text
bot.py                  Application entry point
config.py               Environment config
handlers/               User-facing modules
admin/                  Admin security, permissions, panel, uploads
keyboards/              Inline and persistent keyboard builders
database/               JSON storage, repositories, seeds
database/json_data/     JSON database files
utils/                  Localization and helpers
```

The repository layer is isolated so JSON can later be replaced by PostgreSQL, MongoDB, or another storage backend without rewriting handlers.
