from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field

from sample_model.intent_model import RuleBasedIntentModel
from sample_model.knowledge_base import KnowledgeBase
from sample_model.app_store import ApplicationStore

DATA_DIR = Path(__file__).resolve().parent / "data"

app = FastAPI(title="EV Charging Government Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kb = KnowledgeBase(DATA_DIR / "faq.json")
store = ApplicationStore(DATA_DIR / "applications.json")
model = RuleBasedIntentModel()


class ChatRequest(BaseModel):
    text: str = Field(..., description="User query or message")


class ChatResponse(BaseModel):
    intent: str
    confidence: float
    slots: Dict[str, Any]
    reply: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = model.classify(req.text)
    intent = result["intent"]
    slots = result.get("slots", {})

    # default reply
    reply = "I'm not sure. Try rephrasing or ask for help."

    # FAQ handling
    answer = kb.answer_for_intent(intent)
    if answer:
        reply = answer

    # Status check
    if intent == "status_check" and "app_id" in slots:
        status = store.status_of(slots["app_id"]) 
        if status:
            reply = f"Application {slots['app_id']} status: {status}"
        else:
            reply = f"I couldn't find application {slots['app_id']}. Please check the ID."

    # Progress update
    if intent == "progress_update" and "app_id" in slots and "message" in slots:
        try:
            store.add_progress(slots["app_id"], slots["message"]) 
            reply = f"Progress noted for {slots['app_id']}: {slots['message']}"
        except KeyError:
            reply = f"I couldn't find application {slots['app_id']}. Please check the ID."

    if intent == "greeting":
        reply = "Hello! I can help with EV charging info and applications."
    if intent == "goodbye":
        reply = "Goodbye! Drive electric!"
    if intent == "help":
        reply = "Ask me about finding chargers, costs, incentives, how to apply, or application status like 'status of APP-123456'."

    return ChatResponse(intent=intent, confidence=result["confidence"], slots=slots, reply=reply)


# --- Application endpoints ---
class ApplicationCreate(BaseModel):
    applicant: str
    site_address: str
    power_capacity_kw: int = Field(..., ge=1)
    connectors: List[str]
    contact_email: Optional[EmailStr] = None
    notes: Optional[str] = None


class ApplicationRecord(BaseModel):
    app_id: str
    applicant: str
    status: str
    created_at: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    progress: Optional[List[Dict[str, Any]]] = None


@app.post("/api/applications", response_model=ApplicationRecord)
async def create_application(payload: ApplicationCreate):
    record = store.create_application(
        applicant=payload.applicant,
        site_address=payload.site_address,
        power_capacity_kw=payload.power_capacity_kw,
        connectors=payload.connectors,
        contact_email=payload.contact_email,
        notes=payload.notes,
    )
    return record


@app.get("/api/applications/{app_id}", response_model=ApplicationRecord)
async def get_application(app_id: str):
    rec = store.get_application(app_id)
    if not rec:
        raise HTTPException(404, detail="Application not found")
    return rec


class StatusUpdate(BaseModel):
    status: str


@app.post("/api/applications/{app_id}/status")
async def update_status(app_id: str, payload: StatusUpdate):
    try:
        store.update_status(app_id, payload.status)
    except KeyError:
        raise HTTPException(404, detail="Application not found")
    return {"ok": True}


class ProgressUpdate(BaseModel):
    message: str


@app.post("/api/applications/{app_id}/progress")
async def add_progress(app_id: str, payload: ProgressUpdate):
    try:
        store.add_progress(app_id, payload.message)
    except KeyError:
        raise HTTPException(404, detail="Application not found")
    return {"ok": True}


@app.get("/api/applications")
async def list_applications():
    return store.list_applications()


static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "EV Charging Government Assistant is running."}
