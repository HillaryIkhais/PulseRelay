"""Monitoring agent - evaluates state changes and decides when to alert."""

from typing import Optional

from ..state.models import PatientState, Confidence
from ..state.store import PatientStateStore
from ..state.trends import TrendEngine
from ..safety.rules import SafetyRules


class MonitoringAgent:
    """Evaluates patient state and generates proactive alerts when needed."""

    def __init__(self, store: PatientStateStore):
        self.store = store

    def evaluate(self, session_id: str, latest_event: Optional[dict] = None) -> dict:
        """Evaluate current state and decide what to surface."""
        state = self.store.get_session(session_id)
        if not state:
            return {"action": "none", "message": "No active session"}

        alerts = []
        action = "acknowledge"
        message = ""

        if latest_event:
            if latest_event.get("type") == "incomplete_vital":
                action = "ask"
                message = self._format_incomplete_vital(latest_event)
                alerts.append({
                    "type": "incomplete_vital",
                    "message": message,
                    "severity": "warning",
                })
            elif latest_event.get("type") == "eta":
                action = "alert"
                message = "Transport arriving soon. Handoff preparation initiated."
                alerts.append({
                    "type": "eta",
                    "message": message,
                    "severity": "info",
                })

        trends = TrendEngine.calculate_all_trends(state)
        significant_trends = [
            t for t in trends
            if t.direction.value in ("increasing", "decreasing")
        ]

        if significant_trends and action != "ask":
            trend_messages = []
            for t in significant_trends:
                trend_messages.append(t.message)

            combined = "; ".join(trend_messages)

            if state.latest_bp and state.latest_hr:
                bp_str = f"{state.latest_bp.systolic:.0f}/{state.latest_bp.diastolic:.0f}" if state.latest_bp.is_complete else f"{state.latest_bp.systolic:.0f}/?"
                hr_str = f"{state.latest_hr.value:.0f}"
                message = f"Patient state is changing: {combined}. Current: BP {bp_str}, HR {hr_str}."
            else:
                message = f"Patient state is changing: {combined}"

            action = "alert"
            alerts.append({
                "type": "trend_alert",
                "message": message,
                "severity": "warning",
            })

        completeness_issues = SafetyRules.check_completeness(state)
        if completeness_issues and action == "acknowledge":
            for issue in completeness_issues[:1]:
                if issue.get("type") == "incomplete_vital":
                    action = "ask"
                    message = issue["message"]
                    alerts.append(issue)

        if action == "acknowledge" and latest_event:
            event_type = latest_event.get("type", "")
            if event_type == "vital":
                name = latest_event.get("name", "")
                value = latest_event.get("value", "")
                message = f"{name} {value} recorded."
            elif event_type == "medication":
                name = latest_event.get("name", "")
                dose = latest_event.get("dose", "")
                message = f"{name} {dose} administered."
            elif event_type == "complaint":
                value = latest_event.get("value", "")
                message = f"Chief complaint: {value}."
            else:
                message = "Observation recorded."

        return {
            "action": action,
            "message": message,
            "alerts": alerts,
            "trends": [t.to_dict() for t in trends],
            "state_summary": self._summarize_state(state),
        }

    def _format_incomplete_vital(self, event: dict) -> str:
        name = event.get("name", "vital")
        if name == "BP":
            systolic = event.get("systolic", "")
            return f"I captured systolic {systolic}, but the diastolic value is unclear. Can you repeat the full blood pressure?"
        return f"I couldn't confidently capture the {name}. Can you repeat it?"

    def _summarize_state(self, state: PatientState) -> dict:
        return {
            "demographics": f"{state.demographics.age or '?'}{state.demographics.sex[0].upper() if state.demographics.sex else '?'}",
            "complaint": state.chief_complaint or "Not documented",
            "bp": f"{state.latest_bp.systolic:.0f}/{state.latest_bp.diastolic:.0f}" if state.latest_bp and state.latest_bp.is_complete else "Incomplete",
            "hr": f"{state.latest_hr.value:.0f}" if state.latest_hr else "N/A",
            "pain": f"{state.latest_pain.value:.0f}/10" if state.latest_pain else "N/A",
            "medications": len(state.medications),
            "timeline_events": len(state.timeline),
            "pending_items": len(state.pending_information),
        }
