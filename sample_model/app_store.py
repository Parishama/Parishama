import json
from pathlib import Path
from typing import Dict, List, Optional


class ApplicationStore:
    """JSON file-backed application + progress store for demo purposes."""

    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self._data: Dict[str, Dict[str, object]] = {}
        self._load()

    def _load(self) -> None:
        if not self.store_path.exists():
            self._data = {}
            return
        self._data = json.loads(self.store_path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def upsert_application(self, app_id: str, applicant: str, status: str) -> None:
        record = self._data.get(app_id) or {
            "app_id": app_id,
            "applicant": applicant,
            "status": status,
            "progress": [],
        }
        record["applicant"] = applicant
        record["status"] = status
        self._data[app_id] = record
        self._save()

    def add_progress(self, app_id: str, message: str) -> None:
        record = self._data.get(app_id)
        if not record:
            raise KeyError(f"Unknown application: {app_id}")
        progress: List[Dict[str, str]] = record.get("progress", [])  # type: ignore[assignment]
        progress.append({"message": message})
        record["progress"] = progress
        self._save()

    def get_application(self, app_id: str) -> Optional[Dict[str, object]]:
        return self._data.get(app_id)

    def status_of(self, app_id: str) -> Optional[str]:
        rec = self.get_application(app_id)
        return None if not rec else str(rec.get("status"))
