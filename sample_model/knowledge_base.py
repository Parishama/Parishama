import json
from pathlib import Path
from typing import Dict, Optional


class KnowledgeBase:
    """Simple file-backed FAQ knowledge base."""

    def __init__(self, faq_path: Path) -> None:
        self.faq_path = faq_path
        self.items: Dict[str, Dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        if not self.faq_path.exists():
            self.items = {}
            return
        data = json.loads(self.faq_path.read_text(encoding="utf-8"))
        # Expecting {"faq": [{"id": "", "question": "", "answer": ""}, ...]}
        self.items = {row["id"]: row for row in data.get("faq", [])}

    def get_answer(self, faq_id: str) -> Optional[str]:
        row = self.items.get(faq_id)
        return row.get("answer") if row else None

    # Map intents to FAQ entries
    INTENT_TO_FAQ = {
        "faq_find_station": "find_station",
        "faq_cost": "cost",
        "faq_hours": "hours",
        "faq_incentives": "incentives",
        "faq_requirements": "requirements",
        "apply_how": "apply",
    }

    def answer_for_intent(self, intent: str) -> Optional[str]:
        faq_id = self.INTENT_TO_FAQ.get(intent)
        if not faq_id:
            return None
        return self.get_answer(faq_id)
