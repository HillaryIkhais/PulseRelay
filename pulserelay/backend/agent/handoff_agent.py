"""Handoff agent - generates structured transport summary."""

from ..state.models import PatientState, TrendDirection
from ..state.store import PatientStateStore
from ..state.trends import TrendEngine


class HandoffAgent:
    """Generates structured handoff summaries for receiving hospitals."""

    def __init__(self, store: PatientStateStore):
        self.store = store

    def generate_handoff(self, session_id: str) -> dict:
        """Generate complete transport handoff summary."""
        state = self.store.get_session(session_id)
        if not state:
            return {"error": "No active session"}

        trends = TrendEngine.calculate_all_trends(state)

        initial_vitals = self._get_initial_vitals(state)
        latest_vitals = self._get_latest_vitals(state)

        interventions = []
        for med in state.medications:
            data = med.data if hasattr(med, "data") else med
            interventions.append(f"{data.get('name', 'Unknown')} {data.get('dose', '')}")

        timeline = []
        for event in state.timeline:
            event_data = event.data if hasattr(event, "data") else event
            event_type = event.type.value if hasattr(event.type, "value") else event.get("type", "")
            timestamp = event.timestamp.strftime("%H:%M") if hasattr(event.timestamp, "strftime") else event.get("timestamp", "")
            timeline.append(f"{timestamp} - {event_type}: {event_data}")

        unresolved = []
        for item in state.pending_information:
            unresolved.append(item.get("message", "Unknown pending item"))

        trend_summary = []
        for t in trends:
            if t.direction in (TrendDirection.INCREASING, TrendDirection.DECREASING):
                trend_summary.append(t.message)

        handoff = {
            "patient_info": f"{state.demographics.age or '?'}{state.demographics.sex[0].upper() if state.demographics.sex else '?'}",
            "chief_complaint": state.chief_complaint or "Not documented",
            "initial_vitals": initial_vitals,
            "latest_vitals": latest_vitals,
            "interventions": interventions,
            "trends": trend_summary,
            "timeline": timeline,
            "unresolved_items": unresolved,
            "requires_clinician_review": self._determine_review_needs(state, trends),
        }

        return handoff

    def format_handoff_text(self, session_id: str) -> str:
        """Generate formatted text handoff."""
        handoff = self.generate_handoff(session_id)
        if "error" in handoff:
            return f"Error: {handoff['error']}"

        lines = [
            "=" * 50,
            "PATIENT TRANSPORT SUMMARY",
            "=" * 50,
            "",
            f"Patient: {handoff['patient_info']}",
            f"Chief Complaint: {handoff['chief_complaint']}",
            "",
            "--- Initial Vitals ---",
        ]

        for k, v in handoff["initial_vitals"].items():
            lines.append(f"  {k}: {v}")

        lines.extend(["", "--- Latest Vitals ---"])
        for k, v in handoff["latest_vitals"].items():
            lines.append(f"  {k}: {v}")

        if handoff["interventions"]:
            lines.extend(["", "--- Interventions ---"])
            for intervention in handoff["interventions"]:
                lines.append(f"  - {intervention}")

        if handoff["trends"]:
            lines.extend(["", "--- Trends ---"])
            for trend in handoff["trends"]:
                lines.append(f"  - {trend}")

        if handoff["timeline"]:
            lines.extend(["", "--- Timeline ---"])
            for entry in handoff["timeline"]:
                lines.append(f"  {entry}")

        if handoff["unresolved_items"]:
            lines.extend(["", "--- Items Requiring Clinician Review ---"])
            for item in handoff["unresolved_items"]:
                lines.append(f"  ! {item}")

        if handoff["requires_clinician_review"]:
            lines.extend(["", "--- Alert ---"])
            for alert in handoff["requires_clinician_review"]:
                lines.append(f"  * {alert}")

        lines.extend(["", "=" * 50])
        return "\n".join(lines)

    def _get_initial_vitals(self, state: PatientState) -> dict:
        vitals = {}
        if state.blood_pressures:
            bp = state.blood_pressures[0]
            if bp.is_complete:
                vitals["BP"] = f"{bp.systolic:.0f}/{bp.diastolic:.0f}"
        if state.heart_rates:
            vitals["HR"] = f"{state.heart_rates[0].value:.0f} bpm"
        if state.pain_levels:
            vitals["Pain"] = f"{state.pain_levels[0].value:.0f}/10"
        return vitals

    def _get_latest_vitals(self, state: PatientState) -> dict:
        vitals = {}
        bp = state.latest_bp
        if bp and bp.is_complete:
            vitals["BP"] = f"{bp.systolic:.0f}/{bp.diastolic:.0f}"
        elif bp:
            vitals["BP"] = f"{bp.systolic:.0f}/? (incomplete)"
        hr = state.latest_hr
        if hr:
            vitals["HR"] = f"{hr.value:.0f} bpm"
        pain = state.latest_pain
        if pain:
            vitals["Pain"] = f"{pain.value:.0f}/10"
        return vitals

    def _determine_review_needs(self, state: PatientState, trends: list) -> list[str]:
        needs = []
        for t in trends:
            if t.direction in (TrendDirection.INCREASING, TrendDirection.DECREASING):
                needs.append(f"Hemodynamic trend: {t.message}")
        if state.pending_information:
            needs.append(f"{len(state.pending_information)} incomplete observation(s)")
        return needs
