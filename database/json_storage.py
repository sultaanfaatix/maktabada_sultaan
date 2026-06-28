from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class JsonStorage:
    """Small JSON document store with atomic writes.

    This keeps the first version simple while isolating persistence behind a
    replaceable interface for PostgreSQL, MongoDB, or cloud storage later.
    """

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def path(self, name: str) -> Path:
        return self.base_dir / f"{name}.json"

    def read(self, name: str, default: Any) -> Any:
        path = self.path(name)
        if not path.exists():
            self.write(name, default)
            return default
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def write(self, name: str, payload: Any) -> None:
        path = self.path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        with self._lock:
            with temp.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            temp.replace(path)
