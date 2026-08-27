"""Deterministic patient state store - never derived from LLM output."""

import uuid
from datetime import datetime
from typing import Optional

from .models import (
    BloodPressure,
    Confidence,
    Event,
    EventType,
    PatientDemographics,
    PatientState,
    VitalSign,
)


class PatientStateStore:
    """In-memory patient state store. Firestore integration for persistence."""

    def __init__(self):
        self._sessions: dict[str, PatientState] = {}

    def create_session(self, session_id: Optional[str] = None) -> PatientState:
        sid = session_id or str(uuid.uuid4())
        state = PatientState(session_id=sid, patient_id=sid[:8])
        self._sessions[sid] = state
        return state

    def get_session(self, session_id: str) -> Optional[PatientState]:
        return self._sessions.get(session_id)

    def get_or_create_session(self, session_id: str) -> PatientState:
        if session_id not in self._sessions:
            return self.create_session(session_id)
        return self._sessions[session_id]

    def add_vital(self, session_id: str, vital: VitalSign) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.vitals.append(vital)

        name_lower = vital.name.lower()
        if name_lower in ("hr", "heart_rate", "heart rate", "pulse"):
            state.heart_rates.append(vital)
        elif name_lower in ("pain", "pain_level", "pain level"):
            state.pain_levels.append(vital)

        event = Event(
            id=str(uuid.uuid4()),
            type=EventType.VITAL,
            timestamp=vital.timestamp,
            data=vital.to_dict(),
            confidence=vital.confidence,
            requires_confirmation=vital.requires_confirmation,
            raw_text=vital.raw_text,
        )
        state.add_event(event)
        return state

    def add_blood_pressure(self, session_id: str, bp: BloodPressure) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.blood_pressures.append(bp)

        event = Event(
            id=str(uuid.uuid4()),
            type=EventType.VITAL,
            timestamp=bp.timestamp,
            data=bp.to_dict(),
            confidence=bp.confidence,
            requires_confirmation=bp.requires_confirmation,
            raw_text=bp.raw_text,
        )
        state.add_event(event)
        return state

    def add_medication(self, session_id: str, medication: Event) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.medications.append(medication)
        state.add_event(medication)
        return state

    def add_intervention(self, session_id: str, intervention: Event) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.interventions.append(intervention)
        state.add_event(intervention)
        return state

    def update_demographics(self, session_id: str, demographics: PatientDemographics) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.demographics = demographics
        event = Event(
            id=str(uuid.uuid4()),
            type=EventType.DEMOGRAPHIC,
            timestamp=datetime.now(),
            data=demographics.to_dict(),
        )
        state.add_event(event)
        return state

    def set_chief_complaint(self, session_id: str, complaint: str) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.chief_complaint = complaint
        return state

    def add_pending_information(self, session_id: str, info: dict) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.pending_information.append(info)
        return state

    def resolve_pending_information(self, session_id: str, info_id: str) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.pending_information = [
            p for p in state.pending_information if p.get("id") != info_id
        ]
        return state

    def add_alert(self, session_id: str, alert: dict) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.alerts.append(alert)
        return state

    def clear_alerts(self, session_id: str) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.alerts = []
        return state

    def end_transport(self, session_id: str) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.is_transport_active = False
        return state
