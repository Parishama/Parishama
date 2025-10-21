import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any


class ApplicationStore:
    """JSON file-backed application + progress store for demo purposes."""

    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.store_path.exists():
            self._data = {}
            return
        self._data = json.loads(self.store_path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    # --- Application management ---
    def _generate_new_app_id(self) -> str:
        """Generate a new unique APP-XXXXXX id."""
        # Try a few times to avoid collisions
        for _ in range(1000):
            rand_num = random.randint(100000, 999999)
            app_id = f"APP-{rand_num}"
            if app_id not in self._data:
                return app_id
        # Fallback if somehow all collide
        raise RuntimeError("Unable to generate a unique application id after many attempts")

    def create_application(
        self,
        applicant: str,
        site_address: str,
        power_capacity_kw: int,
        connectors: List[str],
        contact_email: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new application with generated id and initial status.

        Returns the created application record.
        """
        app_id = self._generate_new_app_id()
        created_at = datetime.now(timezone.utc).isoformat()
        record: Dict[str, Any] = {
            "app_id": app_id,
            "applicant": applicant,
            "status": "Received",
            "created_at": created_at,
            "details": {
                "site_address": site_address,
                "power_capacity_kw": int(power_capacity_kw),
                "connectors": list(connectors),
                "contact_email": contact_email,
                "notes": notes,
            },
            "progress": [
                {"timestamp": created_at, "message": "Application received"}
            ],
        }
        self._data[app_id] = record
        self._save()
        return record

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
        progress.append({"timestamp": datetime.now(timezone.utc).isoformat(), "message": message})
        record["progress"] = progress
        self._save()

    def get_application(self, app_id: str) -> Optional[Dict[str, object]]:
        return self._data.get(app_id)

    def status_of(self, app_id: str) -> Optional[str]:
        rec = self.get_application(app_id)
        return None if not rec else str(rec.get("status"))

    def update_status(self, app_id: str, status: str) -> None:
        record = self._data.get(app_id)
        if not record:
            raise KeyError(f"Unknown application: {app_id}")
        record["status"] = status
        # Log status change as progress note
        progress: List[Dict[str, str]] = record.get("progress", [])  # type: ignore[assignment]
        progress.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Status updated to: {status}",
        })
        record["progress"] = progress
        self._save()

    def list_applications(self) -> List[Dict[str, Any]]:
        return list(self._data.values())

    def find_by_applicant(self, applicant_substring: str) -> List[Dict[str, Any]]:
        """Case-insensitive search in applicant field."""
        query = applicant_substring.lower()
        return [r for r in self._data.values() if str(r.get("applicant", "")).lower().find(query) != -1]
