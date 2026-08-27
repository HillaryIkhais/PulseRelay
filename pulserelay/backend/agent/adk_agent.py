"""ADK Agent for PulseRelay - Gemini-powered clinical observation extraction."""

import os
from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from ..state.store import PatientStateStore
from ..state.event_processor import EventProcessor
from ..state.trends import TrendEngine


def extract_observations(session_id: str, text: str) -> dict:
    """Tool to extract clinical observations from text."""
    from ..state.store import PatientStateStore
    from ..state.event_processor import EventProcessor
    
    store = PatientStateStore()
    processor = EventProcessor(store)
    result = processor.process_observation(session_id, text)
    return result


def get_patient_state(session_id: str) -> dict:
    """Tool to get current patient state."""
    from ..state.store import PatientStateStore
    
    store = PatientStateStore()
    state = store.get_session(session_id)
    if state:
        return state.to_dict()
    return {"error": "Session not found"}


def get_vital_trends(session_id: str) -> dict:
    """Tool to calculate vital sign trends."""
    from ..state.store import PatientStateStore
    from ..state.trends import TrendEngine
    
    store = PatientStateStore()
    state = store.get_session(session_id)
    if state:
        trends = TrendEngine.calculate_all_trends(state)
        return {"trends": [t.to_dict() for t in trends]}
    return {"trends": []}


class PulseRelayAgent:
    """ADK-based agent for PulseRelay."""

    def __init__(self):
        self.model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
        
        extract_tool = FunctionTool(
            func=extract_observations,
            name="extract_observations",
            description="Extract clinical observations (BP, HR, pain, medications) from paramedic speech text"
        )
        
        state_tool = FunctionTool(
            func=get_patient_state,
            name="get_patient_state",
            description="Get current patient state including vitals, medications, and timeline"
        )
        
        trends_tool = FunctionTool(
            func=get_vital_trends,
            name="get_vital_trends",
            description="Calculate vital sign trends (increasing, decreasing, stable)"
        )
        
        self.agent = LlmAgent(
            name="PulseRelayAgent",
            model=self.model,
            description="AI agent for paramedic patient transport documentation",
            instruction="""You are PulseRelay, an AI assistant for paramedics during patient transport.

Your role:
1. Receive observations from paramedics (spoken or typed)
2. Extract structured clinical data (BP, HR, pain, medications)
3. Maintain patient state
4. Detect trends and changes
5. Ask for clarification when observations are incomplete
6. Generate handoff summaries

IMPORTANT RULES:
- Never diagnose or recommend treatment
- Never invent missing clinical values
- Always ask for clarification when data is incomplete
- Focus on documentation, not clinical decisions
- Report trends factually without interpretation

When you receive a paramedic observation:
1. Use extract_observations to process the text
2. Check if the extraction was successful
3. If incomplete, ask for clarification
4. If complete, acknowledge the observation
5. Check trends with get_vital_trends if appropriate

For incomplete observations (e.g., "BP 92" without diastolic):
- Report what was captured
- Ask for the missing value
- Never guess or assume the missing value""",
            tools=[extract_tool, state_tool, trends_tool],
        )

    def get_agent(self) -> LlmAgent:
        return self.agent
