"""Trend calculation engine - deterministic, never LLM-derived."""

from datetime import datetime
from typing import Optional

from .models import (
    BloodPressure,
    PatientState,
    VitalSign,
    VitalTrend,
    TrendDirection,
)


class TrendEngine:
    """Calculates vital sign trends deterministically."""

    @staticmethod
    def calculate_bp_trend(state: PatientState) -> Optional[VitalTrend]:
        complete_bps = [bp for bp in state.blood_pressures if bp.is_complete]
        if len(complete_bps) < 2:
            return None

        systolics = [bp.systolic for bp in complete_bps]
        diastolics = [bp.diastolic for bp in complete_bps]
        timestamps = [bp.timestamp.strftime("%H:%M") for bp in complete_bps]

        s_delta = systolics[-1] - systolics[0]
        d_delta = diastolics[-1] - diastolics[0]

        if abs(s_delta) >= 5 or abs(d_delta) >= 5:
            direction = TrendDirection.STABLE
            if s_delta <= -10 or d_delta <= -8:
                direction = TrendDirection.DECREASING
            elif s_delta >= 10 or d_delta >= 8:
                direction = TrendDirection.INCREASING

            return VitalTrend(
                name="BP",
                direction=direction,
                values=systolics,
                timestamps=timestamps,
                delta=s_delta,
                message=f"Systolic {'decreased' if s_delta < 0 else 'increased'} {abs(s_delta):.0f} mmHg",
            )

        return VitalTrend(
            name="BP",
            direction=TrendDirection.STABLE,
            values=systolics,
            timestamps=timestamps,
            delta=0,
            message="Blood pressure stable",
        )

    @staticmethod
    def calculate_hr_trend(state: PatientState) -> Optional[VitalTrend]:
        if len(state.heart_rates) < 2:
            return None

        hrs = [v.value for v in state.heart_rates]
        timestamps = [v.timestamp.strftime("%H:%M") for v in state.heart_rates]

        delta = hrs[-1] - hrs[0]

        if abs(delta) >= 5:
            direction = TrendDirection.INCREASING if delta > 0 else TrendDirection.DECREASING
            return VitalTrend(
                name="HR",
                direction=direction,
                values=hrs,
                timestamps=timestamps,
                delta=delta,
                message=f"Heart rate {'increased' if delta > 0 else 'decreased'} {abs(delta):.0f} bpm",
            )

        return VitalTrend(
            name="HR",
            direction=TrendDirection.STABLE,
            values=hrs,
            timestamps=timestamps,
            delta=0,
            message="Heart rate stable",
        )

    @staticmethod
    def calculate_pain_trend(state: PatientState) -> Optional[VitalTrend]:
        if len(state.pain_levels) < 2:
            return None

        pains = [v.value for v in state.pain_levels]
        timestamps = [v.timestamp.strftime("%H:%M") for v in state.pain_levels]

        delta = pains[-1] - pains[0]

        if abs(delta) >= 1:
            direction = TrendDirection.INCREASING if delta > 0 else TrendDirection.DECREASING
            return VitalTrend(
                name="Pain",
                direction=direction,
                values=pains,
                timestamps=timestamps,
                delta=delta,
                message=f"Pain {'increased' if delta > 0 else 'decreased'} {abs(delta):.0f} points",
            )

        return VitalTrend(
            name="Pain",
            direction=TrendDirection.STABLE,
            values=pains,
            timestamps=timestamps,
            delta=0,
            message="Pain level stable",
        )

    @staticmethod
    def calculate_all_trends(state: PatientState) -> list[VitalTrend]:
        trends = []
        bp = TrendEngine.calculate_bp_trend(state)
        if bp:
            trends.append(bp)
        hr = TrendEngine.calculate_hr_trend(state)
        if hr:
            trends.append(hr)
        pain = TrendEngine.calculate_pain_trend(state)
        if pain:
            trends.append(pain)
        return trends
