"""Clinical safety rules - deterministic state checks."""

from datetime import datetime, timedelta
from typing import Optional

from ..state.models import PatientState, VitalTrend, TrendDirection


class SafetyRules:
    """Checks patient state for conditions requiring attention."""

    @staticmethod
    def check_vital_trends(state: PatientState) -> list[dict]:
        alerts = []

        bp_trend = SafetyRules._check_bp_trend(state)
        if bp_trend:
            alerts.append(bp_trend)

        hr_trend = SafetyRules._check_hr_trend(state)
        if hr_trend:
            alerts.append(hr_trend)

        pain_trend = SafetyRules._check_pain_trend(state)
        if pain_trend:
            alerts.append(pain_trend)

        return alerts

    @staticmethod
    def _check_bp_trend(state: PatientState) -> Optional[dict]:
        if len(state.blood_pressures) < 2:
            return None

        complete_bps = [bp for bp in state.blood_pressures if bp.is_complete]
        if len(complete_bps) < 2:
            return None

        recent = complete_bps[-3:] if len(complete_bps) >= 3 else complete_bps
        systolics = [bp.systolic for bp in recent]

        if len(systolics) >= 2:
            delta = systolics[-1] - systolics[0]
            if delta <= -10:
                return {
                    "type": "trend_alert",
                    "vital": "BP",
                    "direction": "decreasing",
                    "message": f"BP systolic decreased {abs(delta):.0f} mmHg ({systolics[0]:.0f} → {systolics[-1]:.0f})",
                    "severity": "warning",
                    "timestamp": datetime.now().isoformat(),
                }
        return None

    @staticmethod
    def _check_hr_trend(state: PatientState) -> Optional[dict]:
        if len(state.heart_rates) < 2:
            return None

        recent = state.heart_rates[-3:] if len(state.heart_rates) >= 3 else state.heart_rates
        hrs = [v.value for v in recent]

        if len(hrs) >= 2:
            delta = hrs[-1] - hrs[0]
            if abs(delta) >= 10:
                direction = "increasing" if delta > 0 else "decreasing"
                return {
                    "type": "trend_alert",
                    "vital": "HR",
                    "direction": direction,
                    "message": f"Heart rate {direction} {abs(delta):.0f} bpm ({hrs[0]:.0f} → {hrs[-1]:.0f})",
                    "severity": "info",
                    "timestamp": datetime.now().isoformat(),
                }
        return None

    @staticmethod
    def _check_pain_trend(state: PatientState) -> Optional[dict]:
        if len(state.pain_levels) < 2:
            return None

        recent = state.pain_levels[-3:] if len(state.pain_levels) >= 3 else state.pain_levels
        pains = [v.value for v in recent]

        if len(pains) >= 2:
            delta = pains[-1] - pains[0]
            if abs(delta) >= 2:
                direction = "increasing" if delta > 0 else "decreasing"
                return {
                    "type": "trend_alert",
                    "vital": "Pain",
                    "direction": direction,
                    "message": f"Pain level {direction} {abs(delta):.0f} points ({pains[0]:.0f} → {pains[-1]:.0f})",
                    "severity": "warning" if delta > 0 else "info",
                    "timestamp": datetime.now().isoformat(),
                }
        return None

    @staticmethod
    def check_completeness(state: PatientState) -> list[dict]:
        issues = []

        if not state.chief_complaint:
            issues.append({
                "type": "missing_info",
                "field": "chief_complaint",
                "message": "Chief complaint not documented",
            })

        if not state.blood_pressures:
            issues.append({
                "type": "missing_info",
                "field": "blood_pressure",
                "message": "No blood pressure recorded",
            })

        if not state.heart_rates:
            issues.append({
                "type": "missing_info",
                "field": "heart_rate",
                "message": "No heart rate recorded",
            })

        incomplete_bps = [bp for bp in state.blood_pressures if not bp.is_complete]
        for bp in incomplete_bps:
            issues.append({
                "type": "incomplete_vital",
                "field": "blood_pressure",
                "message": f"BP at {bp.timestamp.strftime('%H:%M')} missing diastolic value",
                "timestamp": bp.timestamp.isoformat(),
            })

        return issues

    @staticmethod
    def should_alert(state: PatientState, new_event: dict) -> tuple[bool, str]:
        if new_event.get("type") == "incomplete_vital":
            return True, new_event.get("message", "Incomplete observation captured")

        if new_event.get("type") == "warning":
            return True, new_event.get("message", "Validation warning")

        alerts = SafetyRules.check_vital_trends(state)
        if alerts:
            latest = alerts[-1]
            if latest.get("severity") == "warning":
                return True, latest["message"]

        return False, ""
