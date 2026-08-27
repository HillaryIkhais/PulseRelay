"""Confidence handling - determines certainty of extracted values."""

from ..state.models import Confidence


class ConfidenceCalculator:
    """Calculates confidence based on extraction quality."""

    @staticmethod
    def from_extraction(
        has_value: bool,
        is_complete: bool = True,
        text_quality: str = "clear",
    ) -> Confidence:
        if not has_value:
            return Confidence.UNKNOWN
        if text_quality == "unclear":
            return Confidence.LOW
        if text_quality == "partial":
            return Confidence.MEDIUM
        if not is_complete:
            return Confidence.LOW
        return Confidence.HIGH

    @staticmethod
    def needs_confirmation(confidence: Confidence) -> bool:
        return confidence in (Confidence.LOW, Confidence.UNKNOWN)

    @staticmethod
    def format_clarification_request(
        field: str, partial_value: str = ""
    ) -> str:
        if partial_value:
            return f"I captured {field} as {partial_value}, but I couldn't confirm the complete value. Can you repeat it?"
        return f"I couldn't confidently capture the {field}. Can you repeat it?"
