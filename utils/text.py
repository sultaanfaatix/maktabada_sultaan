from __future__ import annotations


def as_callback_value(value: str) -> str:
    return value.replace(" ", "_")


def from_callback_value(value: str) -> str:
    return value.replace("_", " ")


def paginate(items: list[dict], limit: int = 10) -> list[dict]:
    return items[:limit]
