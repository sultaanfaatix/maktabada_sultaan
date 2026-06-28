from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from database.json_storage import JsonStorage


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ContentRepository:
    def __init__(self, storage: JsonStorage, collection: str) -> None:
        self.storage = storage
        self.collection = collection

    def all(self) -> list[dict[str, Any]]:
        return self.storage.read(self.collection, [])

    def add(self, item: dict[str, Any]) -> dict[str, Any]:
        items = self.all()
        record = {"id": uuid4().hex[:12], "created_at": _now(), **item}
        items.append(record)
        self.storage.write(self.collection, items)
        return record

    def delete(self, item_id: str) -> bool:
        items = self.all()
        kept = [item for item in items if item.get("id") != item_id]
        if len(kept) == len(items):
            return False
        self.storage.write(self.collection, kept)
        return True

    def filter(self, **criteria: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self.all()
            if all(str(item.get(key, "")).casefold() == value.casefold() for key, value in criteria.items())
        ]

    def search(self, query: str) -> list[dict[str, Any]]:
        q = query.casefold().strip()
        if not q:
            return []
        return [
            item
            for item in self.all()
            if q in " ".join(str(value) for value in item.values()).casefold()
        ]


class FeedbackRepository(ContentRepository):
    def __init__(self, storage: JsonStorage) -> None:
        super().__init__(storage, "feedback")


class ResultsRepository:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage

    def all(self) -> dict[str, Any]:
        return self.storage.read("results", {})

    def get_student(self, student_id: str) -> dict[str, Any] | None:
        return self.all().get(student_id.upper())

    def upsert_score(
        self,
        student_id: str,
        name: str,
        grade: str,
        exam_type: str,
        subject: str,
        score: float,
        max_score: float,
    ) -> None:
        data = self.all()
        sid = student_id.upper()
        student = data.setdefault(sid, {"student_id": sid, "name": name, "grades": {}})
        student["name"] = name or student.get("name", "")
        exams = student.setdefault("grades", {}).setdefault(grade, {})
        subjects = exams.setdefault(exam_type, {})
        subjects[subject] = {"score": score, "max_score": max_score, "updated_at": _now()}
        self.storage.write("results", data)


class StatsRepository:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage

    def snapshot(self) -> dict[str, int]:
        return {
            "books": len(self.storage.read("books", [])),
            "exams": len(self.storage.read("exams", [])),
            "lessons": len(self.storage.read("lessons", [])),
            "qa": len(self.storage.read("qa", [])),
            "feedback": len(self.storage.read("feedback", [])),
            "students": len(self.storage.read("results", {})),
        }
