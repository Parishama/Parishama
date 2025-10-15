import re
from typing import Dict, Any, Optional


class RuleBasedIntentModel:
    """Simple rule-based intent classifier for EV charging government assistant.

    Produces a best-effort intent label and extracted slots.
    """

    _APP_ID_RE = re.compile(r"\bAPP-(?:\d{3,8})\b", re.IGNORECASE)

    def __init__(self) -> None:
        # Map intent to list of regex patterns with rough confidence weights
        self.intent_patterns = [
            ("greeting", 0.9, re.compile(r"\b(hi|hello|hey|good\s*(?:morning|afternoon|evening))\b", re.I)),
            ("goodbye", 0.9, re.compile(r"\b(bye|goodbye|see\s*ya|see\s*you)\b", re.I)),
            ("help", 0.8, re.compile(r"\b(help|what\s+can\s+you\s+do|how\s+to\s+use)\b", re.I)),

            # FAQs
            ("faq_find_station", 0.92, re.compile(r"\b(find|nearby|nearest|where)\b.*\b(charger|charging\s*station|ev\s*station|charging)\b", re.I)),
            ("faq_cost", 0.9, re.compile(r"\b(cost|price|pricing|tariff|rate|fees?)\b.*\b(charging|charger|ev)\b|\bcharge\b.*\b(cost|price)\b", re.I)),
            ("faq_hours", 0.85, re.compile(r"\b(hours?|open|24/?7|availability)\b.*\b(charging|station|charger)\b", re.I)),
            ("faq_incentives", 0.88, re.compile(r"\b(grants?|incentives?|subsid(y|ies)|rebates?)\b", re.I)),
            ("faq_requirements", 0.88, re.compile(r"\b(technical\s*requirements?|specs?|power|kw|ocpp|connector|safety|standards?)\b", re.I)),
            ("apply_how", 0.95, re.compile(r"\b(apply|application|set\s*up|setup|install|permit)\b.*\b(charging|station|ev)\b", re.I)),

            # Application specific
            ("status_check", 0.93, re.compile(r"\b(status|track|progress|where\s*is)\b.*\b(APP-\d{3,8})\b", re.I)),
            ("status_check", 0.75, re.compile(r"\bstatus\b.*\b(application)\b", re.I)),
            ("progress_update", 0.96, re.compile(r"\b(update|add|record|log)\b.*\b(progress|update|note)\b.*\b(APP-\d{3,8})\b", re.I)),
            ("progress_update", 0.9, re.compile(r"\bupdate\b\s*(?:progress\s*)?(APP-\d{3,8})\s*[:\-]\s*(.+)$", re.I)),
        ]

    def _extract_app_id(self, text: str) -> Optional[str]:
        match = self._APP_ID_RE.search(text)
        return match.group(0).upper() if match else None

    def _extract_progress_message(self, text: str) -> Optional[str]:
        # Prefer explicit pattern with colon or dash after APP id
        match = re.search(r"(APP-\d{3,8})\s*[:\-]\s*(.+)$", text, re.I)
        if match:
            message = match.group(2).strip()
            return message if message else None
        # If not found, try after the word 'update'
        match = re.search(r"update[\s:,-]+(.+)$", text, re.I)
        if match:
            return match.group(1).strip()
        return None

    def classify(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if not text:
            return {"intent": "empty", "confidence": 1.0, "slots": {}}

        best_intent = "fallback"
        best_conf = 0.1
        for intent, conf, pattern in self.intent_patterns:
            if pattern.search(text):
                if conf > best_conf:
                    best_intent = intent
                    best_conf = conf

        slots: Dict[str, Any] = {}
        app_id = self._extract_app_id(text)
        if app_id:
            slots["app_id"] = app_id
        if best_intent == "progress_update":
            message = self._extract_progress_message(text)
            if message:
                slots["message"] = message

        return {"intent": best_intent, "confidence": round(best_conf, 2), "slots": slots}
