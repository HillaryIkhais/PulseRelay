"""Firestore-backed patient state store for cloud deployment."""

import json
from datetime import datetime
from typing import Optional

from google.cloud import firestore

from .models import (
    BloodPressure,
    Confidence,
    Event,
    EventType,
    PatientDemographics,
    PatientState,
    VitalSign,
)


class FirestorePatientStateStore:
    """Firestore-backed patient state store."""

    def __init__(self, project_id: Optional[str] = None):
        self.db = firestore.Client(project=project_id)
        self.sessions_ref = self.db.collection("sessions")

    def create_session(self, session_id: str) -> PatientState:
        state = PatientState(session_id=session_id, patient_id=session_id[:8])
        self.sessions_ref.document(session_id).set(self._state_to_dict(state))
        return state

    def get_session(self, session_id: str) -> Optional[PatientState]:
        doc = self.sessions_ref.document(session_id).get()
        if not doc.exists:
            return None
        return self._dict_to_state(session_id, doc.to_dict())

    def get_or_create_session(self, session_id: str) -> PatientState:
        state = self.get_session(session_id)
        if state is None:
            state = self.create_session(session_id)
        return state

    def _update_session(self, session_id: str, state: PatientState):
        self.sessions_ref.document(session_id).set(self._state_to_dict(state))

    def add_vital(self, session_id: str, vital: VitalSign) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.vitals.append(vital)

        name_lower = vital.name.lower()
        if name_lower in ("hr", "heart_rate", "heart rate", "pulse"):
            state.heart_rates.append(vital)
        elif name_lower in ("pain", "pain_level", "pain level"):
            state.pain_levels.append(vital)

        event = Event(
            id=f"vital-{len(state.timeline)}",
            type=EventType.VITAL,
            timestamp=vital.timestamp,
            data=vital.to_dict(),
            confidence=vital.confidence,
            requires_confirmation=vital.requires_confirmation,
            raw_text=vital.raw_text,
        )
        state.add_event(event)
        self._update_session(session_id, state)
        return state

    def add_blood_pressure(self, session_id: str, bp: BloodPressure) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.blood_pressures.append(bp)

        event = Event(
            id=f"bp-{len(state.timeline)}",
            type=EventType.VITAL,
            timestamp=bp.timestamp,
            data=bp.to_dict(),
            confidence=bp.confidence,
            requires_confirmation=bp.requires_confirmation,
            raw_text=bp.raw_text,
        )
        state.add_event(event)
        self._update_session(session_id, state)
        return state

    def add_medication(self, session_id: str, medication: Event) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.medications.append(medication)
        state.add_event(medication)
        self._update_session(session_id, state)
        return state

    def add_intervention(self, session_id: str, intervention: Event) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.interventions.append(intervention)
        state.add_event(intervention)
        self._update_session(session_id, state)
        return state

    def update_demographics(self, session_id: str, demographics: PatientDemographics) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.demographics = demographics
        event = Event(
            id=f"demo-{len(state.timeline)}",
            type=EventType.DEMOGRAPHIC,
            timestamp=datetime.now(),
            data=demographics.to_dict(),
        )
        state.add_event(event)
        self._update_session(session_id, state)
        return state

    def set_chief_complaint(self, session_id: str, complaint: str) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.chief_complaint = complaint
        self._update_session(session_id, state)
        return state

    def add_pending_information(self, session_id: str, info: dict) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.pending_information.append(info)
        self._update_session(session_id, state)
        return state

    def resolve_pending_information(self, session_id: str, info_id: str) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.pending_information = [
            p for p in state.pending_information if p.get("id") != info_id
        ]
        self._update_session(session_id, state)
        return state

    def add_alert(self, session_id: str, alert: dict) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.alerts.append(alert)
        self._update_session(session_id, state)
        return state

    def clear_alerts(self, session_id: str) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.alerts = []
        self._update_session(session_id, state)
        return state

    def end_transport(self, session_id: str) -> PatientState:
        state = self.get_or_create_session(session_id)
        state.is_transport_active = False
        self._update_session(session_id, state)
        return state

    def _state_to_dict(self, state: PatientState) -> dict:
        return {
            "session_id": state.session_id,
            "patient_id": state.patient_id,
            "demographics": state.demographics.to_dict(),
            "chief_complaint": state.chief_complaint,
            "vitals": [v.to_dict() for v in state.vitals],
            "blood_pressures": [bp.to_dict() for bp in state.blood_pressures],
            "heart_rates": [v.to_dict() for v in state.heart_rates],
            "pain_levels": [v.to_dict() for v in state.pain_levels],
            "medications": [m.to_dict() for m in state.medications],
            "interventions": [i.to_dict() for i in state.interventions],
            "assessments": [a.to_dict() for a in state.assessments],
            "timeline": [e.to_dict() for e in state.timeline],
            "pending_information": state.pending_information,
            "alerts": state.alerts,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
            "is_transport_active": state.is_transport_active,
        }

    def _dict_to_state(self, session_id: str, data: dict) -> PatientState:
        state = PatientState(
            session_id=session_id,
            patient_id=data.get("patient_id", session_id[:8]),
            chief_complaint=data.get("chief_complaint", ""),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            is_transport_active=data.get("is_transport_active", True),
            pending_information=data.get("pending_information", []),
            alerts=data.get("alerts", []),
        )

        demo_data = data.get("demographics", {})
        state.demographics = PatientDemographics(
            age=demo_data.get("age"),
            sex=demo_data.get("sex"),
            weight=demo_data.get("weight"),
            allergies=demo_data.get("allergies", []),
            medical_history=demo_data.get("medical_history", []),
        )

        for v_data in data.get("vitals", []):
            vital = VitalSign(
                name=v_data["name"],
                value=v_data["value"],
                unit=v_data["unit"],
                timestamp=datetime.fromisoformat(v_data["timestamp"]),
                confidence=Confidence(v_data["confidence"]),
                requires_confirmation=v_data.get("requires_confirmation", False),
                raw_text=v_data.get("raw_text", ""),
            )
            state.vitals.append(vital)

        for bp_data in data.get("blood_pressures", []):
            bp = BloodPressure(
                systolic=bp_data.get("systolic"),
                diastolic=bp_data.get("diastolic"),
                timestamp=datetime.fromisoformat(bp_data["timestamp"]),
                confidence=Confidence(bp_data["confidence"]),
                requires_confirmation=bp_data.get("requires_confirmation", False),
                raw_text=bp_data.get("raw_text", ""),
            )
            state.blood_pressures.append(bp)

        for v_data in data.get("heart_rates", []):
            vital = VitalSign(
                name=v_data["name"],
                value=v_data["value"],
                unit=v_data["unit"],
                timestamp=datetime.fromisoformat(v_data["timestamp"]),
                confidence=Confidence(v_data["confidence"]),
                requires_confirmation=v_data.get("requires_confirmation", False),
                raw_text=v_data.get("raw_text", ""),
            )
            state.heart_rates.append(vital)

        for v_data in data.get("pain_levels", []):
            vital = VitalSign(
                name=v_data["name"],
                value=v_data["value"],
                unit=v_data["unit"],
                timestamp=datetime.fromisoformat(v_data["timestamp"]),
                confidence=Confidence(v_data["confidence"]),
                requires_confirmation=v_data.get("requires_confirmation", False),
                raw_text=v_data.get("raw_text", ""),
            )
            state.pain_levels.append(vital)

        for m_data in data.get("medications", []):
            event = Event(
                id=m_data["id"],
                type=EventType(m_data["type"]),
                timestamp=datetime.fromisoformat(m_data["timestamp"]),
                data=m_data["data"],
                confidence=Confidence(m_data["confidence"]),
                requires_confirmation=m_data.get("requires_confirmation", False),
                raw_text=m_data.get("raw_text", ""),
            )
            state.medications.append(event)

        for e_data in data.get("timeline", []):
            event = Event(
                id=e_data["id"],
                type=EventType(e_data["type"]),
                timestamp=datetime.fromisoformat(e_data["timestamp"]),
                data=e_data["data"],
                confidence=Confidence(e_data["confidence"]),
                requires_confirmation=e_data.get("requires_confirmation", False),
                raw_text=e_data.get("raw_text", ""),
            )
            state.timeline.append(event)

        return state
