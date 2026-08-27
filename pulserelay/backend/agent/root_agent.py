"""Root agent - orchestrates extraction, monitoring, and handoff."""

from typing import Optional

from ..state.store import PatientStateStore
from ..state.event_processor import EventProcessor
from ..safety.validation import VitalValidator
from ..safety.confidence import ConfidenceCalculator
from .extraction_agent import ExtractionAgent
from .monitoring_agent import MonitoringAgent
from .handoff_agent import HandoffAgent


class PulseRelayAgent:
    """Root agent coordinating the full workflow."""

    def __init__(self):
        self.store = PatientStateStore()
        self.processor = EventProcessor(self.store)
        self.extraction = ExtractionAgent(self.store, self.processor)
        self.monitoring = MonitoringAgent(self.store)
        self.handoff = HandoffAgent(self.store)

    def process_observation(self, session_id: str, text: str) -> dict:
        """Full pipeline: extract -> validate -> store -> evaluate -> respond."""
        extraction_result = self.extraction.extract(session_id, text)

        monitoring_result = self.monitoring.evaluate(
            session_id,
            latest_event=extraction_result["results"]["events_created"][0]
            if extraction_result["results"]["events_created"]
            else None,
        )

        return {
            "extraction": extraction_result,
            "monitoring": monitoring_result,
            "state": self.store.get_session(session_id).to_dict()
            if self.store.get_session(session_id)
            else None,
        }

    def get_state(self, session_id: str) -> Optional[dict]:
        state = self.store.get_session(session_id)
        return state.to_dict() if state else None

    def get_handoff(self, session_id: str) -> dict:
        return self.handoff.generate_handoff(session_id)

    def get_handoff_text(self, session_id: str) -> str:
        return self.handoff.format_handoff_text(session_id)

    def start_session(self, session_id: str) -> dict:
        state = self.store.create_session(session_id)
        return {"session_id": session_id, "status": "created"}

    def get_trends(self, session_id: str) -> list[dict]:
        from ..state.trends import TrendEngine
        state = self.store.get_session(session_id)
        if not state:
            return []
        trends = TrendEngine.calculate_all_trends(state)
        return [t.to_dict() for t in trends]
