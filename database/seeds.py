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
    "exam_types": ["Monthly 1", "Monthly 2", "Mid-term 1", "Mid-term 2", "Final Exam"],
}
