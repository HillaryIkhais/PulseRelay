"""API routes for PulseRelay."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..agent.root_agent import PulseRelayAgent


class ObservationRequest(BaseModel):
    session_id: str
    text: str


class SessionRequest(BaseModel):
    session_id: Optional[str] = None


router = APIRouter()
agent = PulseRelayAgent()


@router.post("/session/start")
async def start_session(req: SessionRequest):
    import uuid
    session_id = req.session_id or str(uuid.uuid4())
    result = agent.start_session(session_id)
    return result


@router.post("/observe")
async def observe(req: ObservationRequest):
    result = agent.process_observation(req.session_id, req.text)
    return result


@router.get("/state/{session_id}")
async def get_state(session_id: str):
    state = agent.get_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


@router.get("/trends/{session_id}")
async def get_trends(session_id: str):
    trends = agent.get_trends(session_id)
    return {"trends": trends}


@router.get("/handoff/{session_id}")
async def get_handoff(session_id: str):
    handoff = agent.get_handoff(session_id)
    return handoff


@router.get("/handoff/{session_id}/text")
async def get_handoff_text(session_id: str):
    text = agent.get_handoff_text(session_id)
    return {"handoff": text}


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "PulseRelay"}
