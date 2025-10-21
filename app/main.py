from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from sample_model.intent_model import RuleBasedIntentModel
from sample_model.knowledge_base import KnowledgeBase
from sample_model.app_store import ApplicationStore


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
WEB_DIR = BASE_DIR / "web"


app = FastAPI(title="EV Charging Government Assistant", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
kb = KnowledgeBase(DATA_DIR / "faq.json")
store = ApplicationStore(DATA_DIR / "applications.json")
model = RuleBasedIntentModel()


class ChatRequest(BaseModel):
    text: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str
    intent: str
    confidence: float
    slots: Dict[str, Any]
    application_status: Optional[str] = None
    progress_recorded: bool = False


class CreateApplicationRequest(BaseModel):
    applicant: str = Field(..., min_length=2)
    site_address: Optional[str] = None
    connectors: Optional[str] = Field(
        default=None,
        description="Connector types requested, e.g., CCS, Type 2, CHAdeMO",
    )
    power_kw: Optional[int] = Field(default=None, ge=1, le=1000)
    notes: Optional[str] = None


class CreateApplicationResponse(BaseModel):
    app_id: str
    status: str


class ProgressRequest(BaseModel):
    message: str = Field(..., min_length=2)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    result = model.classify(req.text)
    intent = result["intent"]
    confidence = float(result.get("confidence", 0.0))
    slots = dict(result.get("slots", {}))

    reply_parts: list[str] = []
    progress_recorded = False
    application_status: Optional[str] = None

    # FAQ intents
    answer = kb.answer_for_intent(intent)
    if answer:
        reply_parts.append(answer)

    # Status check
    if intent == "status_check" and "app_id" in slots:
        status = store.status_of(slots["app_id"])  # type: ignore[index]
        if status:
            application_status = status
            reply_parts.append(f"Application {slots['app_id']} status: {status}")
        else:
            reply_parts.append(
                f"I couldn't find application {slots['app_id']}. Please check the ID."
            )

    # Progress update
    if intent == "progress_update" and "app_id" in slots and "message" in slots:
        try:
            store.add_progress(slots["app_id"], slots["message"])  # type: ignore[index]
            progress_recorded = True
            reply_parts.append(
                f"Progress noted for {slots['app_id']}: {slots['message']}"
            )
        except KeyError:
            reply_parts.append(
                f"I couldn't find application {slots['app_id']}. Please check the ID."
            )

    if intent == "greeting":
        reply_parts.append(
            "Hello! I can help with EV charging info and applications."
        )
    if intent == "goodbye":
        reply_parts.append("Goodbye! Drive electric!")
    if intent == "help":
        reply_parts.append(
            "Ask me about finding chargers, costs, incentives, how to apply, or application status like 'status of APP-123456'."
        )

    if not reply_parts:
        reply_parts.append("I'm not sure. Try rephrasing or ask for help.")

    return ChatResponse(
        reply="\n".join(reply_parts),
        intent=intent,
        confidence=confidence,
        slots=slots,
        application_status=application_status,
        progress_recorded=progress_recorded,
    )


def _generate_app_id() -> str:
    # Keep generating until unique
    for _ in range(100):
        num = random.randint(100000, 999999)
        app_id = f"APP-{num}"
        if not store.get_application(app_id):
            return app_id
    raise RuntimeError("Unable to generate a unique application ID")


@app.post("/api/applications", response_model=CreateApplicationResponse)
def create_application(req: CreateApplicationRequest) -> CreateApplicationResponse:
    app_id = _generate_app_id()
    status = "Submitted"
    store.upsert_application(app_id=app_id, applicant=req.applicant, status=status)

    # Record details as initial progress notes for transparency
    details_parts: list[str] = []
    if req.site_address:
        details_parts.append(f"site: {req.site_address}")
    if req.connectors:
        details_parts.append(f"connectors: {req.connectors}")
    if req.power_kw:
        details_parts.append(f"power_kW: {req.power_kw}")
    if req.notes:
        details_parts.append(f"notes: {req.notes}")
    if details_parts:
        store.add_progress(app_id, "Application details - " + "; ".join(details_parts))
    store.add_progress(app_id, f"Submitted by {req.applicant}")

    return CreateApplicationResponse(app_id=app_id, status=status)


@app.get("/api/applications/{app_id}")
def get_application(app_id: str) -> Dict[str, Any]:
    record = store.get_application(app_id)
    if not record:
        raise HTTPException(status_code=404, detail="Application not found")
    return record


@app.post("/api/applications/{app_id}/progress")
def add_progress(app_id: str, req: ProgressRequest) -> Dict[str, Any]:
    try:
        store.add_progress(app_id, req.message)
        return {"ok": True}
    except KeyError:
        raise HTTPException(status_code=404, detail="Application not found")


# Static/frontend
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not built")
    return FileResponse(str(index_path))
