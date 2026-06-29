from __future__ import annotations

from utils.i18n import LEVEL_LABELS


DEFAULT_PLATFORM_SETTINGS = {
    "levels": {
        "primary": {
            "label": LEVEL_LABELS["primary"],
            "classes": ["1aad", "2aad", "3aad", "4aad"],
            "subjects": ["Xisaab", "Saynis", "Cilmi Bulsho", "Carabi", "English", "Af Soomaali", "Tarbiya Islaamka"],
        },
        "middle": {
            "label": LEVEL_LABELS["middle"],
            "classes": ["5aad", "6aad", "7aad", "8aad"],
            "subjects": ["Xisaab", "Saynis", "Cilmi Bulsho", "Carabi", "English", "Af Soomaali", "Tarbiya Islaamka", "Technology"],
        },
        "secondary": {
            "label": LEVEL_LABELS["secondary"],
            "classes": ["Form 1", "Form 2", "Form 3", "Form 4"],
            "subjects": [
                "Mathematics",
                "Physics",
                "Biology",
                "Chemistry",
                "English",
                "Af Soomaali",
                "Carabi",
                "Tarbiya Islaamka",
                "Taariikh",
                "Juqraafi",
                "Business",
                "Technology",
            ],
        },
    },
    "book_types": ["Student Book", "Teacher Guide", "Revision"],
    "exam_classes": ["8aad", "Form 4"],
    "exam_years": [
        "2015-2016",
        "2016-2017",
        "2017-2018",
        "2018-2019",
        "2019-2020",
        "2020-2021",
        "2021-2022",
        "2022-2023",
        "2023-2024",
        "2024-2025",
        "2025-2026",
    ],
    "lesson_classes": ["Form 1", "Form 2", "Form 3", "Form 4"],
    "result_classes": ["7aad", "8aad", "Form 1", "Form 2", "Form 3", "Form 4"],
    "qa_classes": ["5aad", "6aad", "7aad", "8aad", "Form 1", "Form 2", "Form 3", "Form 4"],
    "exam_types": ["Monthly 1", "Monthly 2", "Mid-term 1", "Monthly 3", "Monthly 4", "Final Exam"],
}


DEFAULT_ABOUT_PROFILE = {
    "founder_name": "Sultaan",
    "founder_title": "Founder & Education Platform Lead",
    "organization": "MAKTABADA SULTAAN",
    "mission": "In la fududeeyo helitaanka buugaag, imtixaanno, casharro, natiijooyin iyo muraajaco tayo leh oo macallimiin iyo arday kasta gaadhi karaan.",
    "description": "MAKTABADA SULTAAN waa madal waxbarasho oo Telegram ku shaqeysa, looguna talagalay ardayda, macallimiinta iyo waalidiinta.",

    "contact": {
        "phone": {
            "display": "+252 61 9568689",
            "call_link": "tel:+252619568689"
        },
        "whatsapp": {
            "display": "+252 68 4613207",
            "chat_link": "https://wa.me/252684613207"
        },
        "email": "sultaanfaatix@gmail.com",
        "telegram": "@MAKTABADA SULTAAN 📚"
    },

    "social_links": {
        "telegram": "https://t.me/SultanLibraryBot",
        "facebook": "https://www.facebook.com/sultaanfaatix",
    },

    "photo_file_id": "",
    "logo_file_id": ""
}