from __future__ import annotations

import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from database.json_storage import JsonStorage
from database.seeds import DEFAULT_ABOUT_PROFILE, DEFAULT_PLATFORM_SETTINGS
from utils.i18n import ALL_PERMISSIONS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _class_alias(value: str) -> str:
    text = str(value).strip()
    if text.endswith("aad") and text[:-3].isdigit():
        return text[:-3]
    if text.isdigit():
        return f"{text}aad"
    return text


class ContentRepository:
    def __init__(self, storage: JsonStorage, collection: str) -> None:
        self.storage = storage
        self.collection = collection

    def all(self) -> list[dict[str, Any]]:
        return self.storage.read(self.collection, [])

    def add(self, item: dict[str, Any]) -> dict[str, Any]:
        items = self.all()
        record = {"id": uuid4().hex[:12], "created_at": _now(), "downloads": 0, **item}
        items.append(record)
        self.storage.write(self.collection, items)
        return record

    def update(self, item_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        items = self.all()
        for item in items:
            if item.get("id") == item_id:
                item.update(changes)
                item["updated_at"] = _now()
                self.storage.write(self.collection, items)
                return item
        return None

    def increment(self, item_id: str, field: str) -> None:
        items = self.all()
        for item in items:
            if item.get("id") == item_id:
                item[field] = int(item.get(field, 0)) + 1
                self.storage.write(self.collection, items)
                return

    def delete(self, item_id: str) -> bool:
        items = self.all()
        kept = [item for item in items if item.get("id") != item_id]
        if len(kept) == len(items):
            return False
        self.storage.write(self.collection, kept)
        return True

    def filter(self, **criteria: str) -> list[dict[str, Any]]:
        matches = []
        for item in self.all():
            ok = True
            for key, value in criteria.items():
                actual = str(item.get(key, ""))
                expected = str(value)
                if key == "grade" and actual.casefold() not in {expected.casefold(), _class_alias(expected).casefold()}:
                    ok = False
                    break
                if key != "grade" and actual.casefold() != expected.casefold():
                    ok = False
                    break
            if ok:
                matches.append(item)
        return matches

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


class PlatformSettingsRepository:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage

    def get(self) -> dict[str, Any]:
        current = self.storage.read("platform_settings", DEFAULT_PLATFORM_SETTINGS)
        merged = self._merge_defaults(current)
        if merged != current:
            self.storage.write("platform_settings", merged)
        return merged

    def _merge_defaults(self, current: dict[str, Any]) -> dict[str, Any]:
        merged = {**DEFAULT_PLATFORM_SETTINGS, **current}
        levels = {**DEFAULT_PLATFORM_SETTINGS["levels"], **current.get("levels", {})}
        for key, defaults in DEFAULT_PLATFORM_SETTINGS["levels"].items():
            configured = levels.get(key, {})
            classes = list(dict.fromkeys(configured.get("classes", defaults["classes"])))
            subjects = list(dict.fromkeys(configured.get("subjects", defaults["subjects"])))
            if key == "primary" and "5aad" in classes:
                classes.remove("5aad")
            if key in {"primary", "middle"} and "Cilmi Bulsho" not in subjects:
                subjects.insert(2, "Cilmi Bulsho")
            levels[key] = {**defaults, **configured, "classes": classes, "subjects": subjects}
        merged["levels"] = levels
        for key, value in DEFAULT_PLATFORM_SETTINGS.items():
            if isinstance(value, list):
                merged[key] = list(dict.fromkeys([*value, *current.get(key, [])]))
        return merged

    def classes_for_level(self, level: str) -> list[str]:
        return self.get()["levels"][level]["classes"]

    def subjects_for_level(self, level: str) -> list[str]:
        return self.get()["levels"][level]["subjects"]

    def level_by_label(self, label: str) -> str:
        for key, meta in self.get()["levels"].items():
            if meta["label"] == label:
                return key
        raise KeyError(label)

    def level_for_class(self, class_name: str) -> str:
        for key, meta in self.get()["levels"].items():
            if class_name in meta["classes"]:
                return key
        return "secondary" if class_name.startswith("Form") else "middle"

    def add_subject(self, level: str, subject: str) -> None:
        data = self.get()
        subjects = data["levels"][level]["subjects"]
        if subject not in subjects:
            subjects.append(subject)
            self.storage.write("platform_settings", data)

    def rename_subject(self, level: str, old: str, new: str) -> bool:
        data = self.get()
        subjects = data["levels"][level]["subjects"]
        if old not in subjects:
            return False
        subjects[subjects.index(old)] = new
        self.storage.write("platform_settings", data)
        return True

    def delete_subject(self, level: str, subject: str) -> bool:
        data = self.get()
        subjects = data["levels"][level]["subjects"]
        if subject not in subjects:
            return False
        subjects.remove(subject)
        self.storage.write("platform_settings", data)
        return True

    def add_class(self, level: str, class_name: str) -> None:
        data = self.get()
        classes = data["levels"][level]["classes"]
        if class_name not in classes:
            classes.append(class_name)
            self.storage.write("platform_settings", data)

    def rename_class(self, level: str, old: str, new: str) -> bool:
        data = self.get()
        classes = data["levels"][level]["classes"]
        if old not in classes:
            return False
        classes[classes.index(old)] = new
        self.storage.write("platform_settings", data)
        return True

    def delete_class(self, level: str, class_name: str) -> bool:
        data = self.get()
        classes = data["levels"][level]["classes"]
        if class_name not in classes:
            return False
        classes.remove(class_name)
        self.storage.write("platform_settings", data)
        return True

    def add_year(self, year: str) -> None:
        data = self.get()
        if year not in data["exam_years"]:
            data["exam_years"].append(year)
            data["exam_years"].sort()
            self.storage.write("platform_settings", data)

    def rename_year(self, old: str, new: str) -> bool:
        data = self.get()
        if old not in data["exam_years"]:
            return False
        data["exam_years"][data["exam_years"].index(old)] = new
        data["exam_years"].sort()
        self.storage.write("platform_settings", data)
        return True

    def delete_year(self, year: str) -> bool:
        data = self.get()
        if year not in data["exam_years"]:
            return False
        data["exam_years"].remove(year)
        self.storage.write("platform_settings", data)
        return True


class AdminRepository:
    def __init__(self, storage: JsonStorage, owner_id: int) -> None:
        self.storage = storage
        self.owner_id = str(owner_id)

    def all(self) -> dict[str, Any]:
        admins = self.storage.read("admins", {})
        owner = admins.setdefault(
            self.owner_id,
            {"user_id": int(self.owner_id), "role": "owner", "permissions": ALL_PERMISSIONS, "created_at": _now()},
        )
        owner["permissions"] = ALL_PERMISSIONS
        self.storage.write("admins", admins)
        return admins

    def is_admin(self, user_id: int | None) -> bool:
        return bool(user_id and str(user_id) in self.all())

    def has_permission(self, user_id: int | None, permission: str) -> bool:
        if not user_id:
            return False
        admin = self.all().get(str(user_id))
        return bool(admin and (admin.get("role") == "owner" or permission in admin.get("permissions", [])))

    def add(self, user_id: int, permissions: list[str]) -> dict[str, Any]:
        admins = self.all()
        admins[str(user_id)] = {
            "user_id": user_id,
            "role": "custom",
            "permissions": [p for p in permissions if p in ALL_PERMISSIONS],
            "created_at": _now(),
        }
        self.storage.write("admins", admins)
        return admins[str(user_id)]

    def remove(self, user_id: int) -> bool:
        if str(user_id) == self.owner_id:
            return False
        admins = self.all()
        if str(user_id) not in admins:
            return False
        del admins[str(user_id)]
        self.storage.write("admins", admins)
        return True


class AnalyticsRepository:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage

    def track_user(self, user_id: int | None, username: str | None = None) -> None:
        if not user_id:
            return
        data = self.storage.read("analytics", {"users": {}, "events": [], "downloads": {}})
        today = date.today().isoformat()
        user = data["users"].setdefault(str(user_id), {"first_seen": _now(), "username": username, "days": []})
        user["last_seen"] = _now()
        user["username"] = username
        if today not in user["days"]:
            user["days"].append(today)
        self.storage.write("analytics", data)

    def event(self, user_id: int | None, name: str, meta: dict[str, Any] | None = None) -> None:
        data = self.storage.read("analytics", {"users": {}, "events": [], "downloads": {}})
        data["events"].append({"user_id": user_id, "name": name, "meta": meta or {}, "created_at": _now()})
        data["events"] = data["events"][-1000:]
        self.storage.write("analytics", data)

    def download(self, collection: str, item: dict[str, Any]) -> None:
        data = self.storage.read("analytics", {"users": {}, "events": [], "downloads": {}})
        key = f"{collection}:{item.get('id')}"
        metric = data["downloads"].setdefault(key, {"title": item.get("title", item.get("id")), "collection": collection, "count": 0})
        metric["count"] += 1
        self.storage.write("analytics", data)

    def snapshot(self) -> dict[str, Any]:
        data = self.storage.read("analytics", {"users": {}, "events": [], "downloads": {}})
        today = date.today().isoformat()
        return {
            "users_total": len(data["users"]),
            "daily_active_users": sum(1 for user in data["users"].values() if today in user.get("days", [])),
            "events": len(data["events"]),
            "top_downloads": sorted(data["downloads"].values(), key=lambda item: item["count"], reverse=True)[:5],
        }

    def data(self) -> dict[str, Any]:
        return self.storage.read("analytics", {"users": {}, "events": [], "downloads": {}})

    def users(self, query: str = "") -> list[dict[str, Any]]:
        data = self.data()
        users = [{"user_id": user_id, **payload} for user_id, payload in data["users"].items()]
        if query:
            q = query.casefold()
            users = [user for user in users if q in str(user).casefold()]
        return sorted(users, key=lambda user: user.get("last_seen", ""), reverse=True)

    def events(self, query: str = "") -> list[dict[str, Any]]:
        events = list(reversed(self.data()["events"]))
        if query:
            q = query.casefold()
            events = [event for event in events if q in str(event).casefold()]
        return events

    def downloads(self, collection: str | None = None) -> list[dict[str, Any]]:
        downloads = list(self.data()["downloads"].values())
        if collection:
            downloads = [item for item in downloads if item.get("collection") == collection]
        return sorted(downloads, key=lambda item: item["count"], reverse=True)


class ActivityLogRepository(ContentRepository):
    def __init__(self, storage: JsonStorage) -> None:
        super().__init__(storage, "activity_log")

    def log(self, user_id: int | None, action: str, meta: dict[str, Any] | None = None) -> None:
        self.add({"user_id": user_id, "action": action, "meta": meta or {}})


class BackupRepository:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage

    def create(self) -> Path:
        backup_dir = self.storage.base_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        destination = backup_dir / f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        destination.mkdir()
        for path in self.storage.base_dir.glob("*.json"):
            shutil.copy2(path, destination / path.name)
        return destination


class AboutRepository:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage

    def get(self) -> dict[str, Any]:
        current = self.storage.read("about_profile", DEFAULT_ABOUT_PROFILE)
        merged = {**DEFAULT_ABOUT_PROFILE, **current}
        merged["contact"] = {**DEFAULT_ABOUT_PROFILE["contact"], **current.get("contact", {})}
        merged["social_links"] = {**DEFAULT_ABOUT_PROFILE["social_links"], **current.get("social_links", {})}
        if merged != current:
            self.storage.write("about_profile", merged)
        return merged

    def update(self, changes: dict[str, Any]) -> None:
        profile = self.get()
        profile.update(changes)
        self.storage.write("about_profile", profile)


class StatsRepository:
    def __init__(self, storage: JsonStorage) -> None:
        self.storage = storage

    def snapshot(self) -> dict[str, int]:
        analytics = AnalyticsRepository(self.storage).snapshot()
        return {
            "books": len(self.storage.read("books", [])),
            "exams": len(self.storage.read("exams", [])),
            "lessons": len(self.storage.read("lessons", [])),
            "qa": len(self.storage.read("qa", [])),
            "feedback": len(self.storage.read("feedback", [])),
            "students": len(self.storage.read("results", {})),
            "users_total": analytics["users_total"],
            "daily_active_users": analytics["daily_active_users"],
        }
