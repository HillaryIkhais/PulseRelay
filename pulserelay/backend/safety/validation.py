"""Vital sign validation rules - deterministic, never LLM-derived."""

from typing import Optional

from ..state.models import Confidence, VitalSign, BloodPressure


class VitalValidator:
    """Validates vital signs against clinical ranges."""

    RANGES = {
        "hr": {"min": 30, "max": 300, "unit": "bpm"},
        "heart_rate": {"min": 30, "max": 300, "unit": "bpm"},
        "pulse": {"min": 30, "max": 300, "unit": "bpm"},
        "bp_systolic": {"min": 40, "max": 300, "unit": "mmHg"},
        "bp_diastolic": {"min": 20, "max": 200, "unit": "mmHg"},
        "pain": {"min": 0, "max": 10, "unit": "/10"},
        "spo2": {"min": 0, "max": 100, "unit": "%"},
        "resp_rate": {"min": 5, "max": 60, "unit": "breaths/min"},
        "temperature": {"min": 85, "max": 110, "unit": "F"},
    }

    @classmethod
    def validate_vital(cls, vital: VitalSign) -> VitalSign:
        vital_name = vital.name.lower().replace(" ", "_")
        if vital_name in cls.RANGES:
            r = cls.RANGES[vital_name]
            if not (r["min"] <= vital.value <= r["max"]):
                vital.confidence = Confidence.LOW
                vital.requires_confirmation = True
        return vital

    @classmethod
    def validate_bp(cls, bp: BloodPressure) -> BloodPressure:
        if bp.systolic is not None:
            if not (40 <= bp.systolic <= 300):
                bp.confidence = Confidence.LOW
                bp.requires_confirmation = True
        if bp.diastolic is not None:
            if not (20 <= bp.diastolic <= 200):
                bp.confidence = Confidence.LOW
                bp.requires_confirmation = True
        if bp.systolic is not None and bp.diastolic is not None:
            if bp.systolic <= bp.diastolic:
                bp.confidence = Confidence.LOW
                bp.requires_confirmation = True
        return bp

    @classmethod
    def is_clinically_significant_change(
        cls, old: float, new: float, vital_name: str
    ) -> bool:
        vital_name = vital_name.lower().replace(" ", "_")
        if vital_name in ("hr", "heart_rate", "pulse"):
            return abs(new - old) >= 10
        if vital_name == "bp_systolic":
            return abs(new - old) >= 10
        if vital_name == "bp_diastolic":
            return abs(new - old) >= 8
        if vital_name == "pain":
            return abs(new - old) >= 2
        if vital_name == "spo2":
            return abs(new - old) >= 3
        return False
