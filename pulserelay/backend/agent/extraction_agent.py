"""Extraction agent - uses Gemini for NLU, deterministic code for values."""

import json
import os
from typing import Optional

import google.generativeai as genai

from ..state.event_processor import EventProcessor
from ..state.store import PatientStateStore


class ExtractionAgent:
    """Extracts structured observations from paramedic speech using Gemini."""

    def __init__(self, store: PatientStateStore, processor: EventProcessor):
        self.store = store
        self.processor = processor
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-3.5-flash")
        else:
            self.model = None

    def extract(self, session_id: str, text: str) -> dict:
        """Extract observations from text. Uses regex first, Gemini for complex cases."""
        regex_results = self.processor.process_observation(session_id, text)

        if regex_results["events_created"]:
            return {
                "method": "regex",
                "results": regex_results,
                "raw_text": text,
            }

        if self.model:
            return self._extract_with_gemini(session_id, text)

        return {
            "method": "none",
            "results": {"events_created": [], "warnings": ["No extraction method available"]},
            "raw_text": text,
        }

    def _extract_with_gemini(self, session_id: str, text: str) -> dict:
        """Use Gemini for complex extraction, then validate deterministically."""
        prompt = f"""Extract clinical observations from this paramedic statement.
Return ONLY a JSON array of observation objects. No other text.

Statement: "{text}"

Each observation object should have:
- "type": one of "vital", "medication", "symptom", "demographic"
- "name": the specific measurement (e.g., "BP", "HR", "Pain", "Aspirin")
- "value": the numeric or string value
- "unit": the unit if applicable
- "confidence": "high", "medium", or "low"
- "notes": any qualifiers (e.g., "patient reports")

If a value is partially stated or unclear, set confidence to "low" and include what was heard in notes.

Examples:
- "BP 104 over 67" -> [{{"type": "vital", "name": "BP", "value": "104/67", "unit": "mmHg", "confidence": "high"}}]
- "heart rate 118" -> [{{"type": "vital", "name": "HR", "value": 118, "unit": "bpm", "confidence": "high"}}]
- "pain 7 out of 10" -> [{{"type": "vital", "name": "Pain", "value": 7, "unit": "/10", "confidence": "high"}}]
- "aspirin administered 324 mg" -> [{{"type": "medication", "name": "Aspirin", "value": "324mg", "confidence": "high"}}]
- "BP ninety-two" -> [{{"type": "vital", "name": "BP_systolic", "value": 92, "confidence": "low", "notes": "diastolic not stated"}}]
"""
        try:
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            observations = json.loads(content)
        except Exception as e:
            return {
                "method": "gemini_error",
                "results": {"events_created": [], "warnings": [f"Gemini error: {str(e)}"]},
                "raw_text": text,
            }

        events = []
        for obs in observations:
            result = self._process_gemini_observation(session_id, obs)
            if result:
                events.append(result)

        return {
            "method": "gemini",
            "results": {"events_created": events, "warnings": []},
            "raw_text": text,
        }

    def _process_gemini_observation(self, session_id: str, obs: dict) -> Optional[dict]:
        """Process a Gemini-extracted observation through deterministic validation."""
        obs_type = obs.get("type", "")
        name = obs.get("name", "")
        value = obs.get("value")
        confidence = obs.get("confidence", "high")

        if obs_type == "vital" and name in ("BP", "blood_pressure"):
            if isinstance(value, str) and "/" in value:
                parts = value.split("/")
                try:
                    systolic = float(parts[0])
                    diastolic = float(parts[1])
                    from ..state.models import BloodPressure, Confidence
                    bp = BloodPressure(
                        systolic=systolic,
                        diastolic=diastolic,
                        timestamp=__import__("datetime").datetime.now(),
                        confidence=Confidence.HIGH if confidence == "high" else Confidence.MEDIUM,
                        raw_text=obs.get("notes", ""),
                    )
                    self.store.add_blood_pressure(session_id, bp)
                    return {"type": "vital", "name": "BP", "value": f"{systolic}/{diastolic}", "confidence": confidence}
                except (ValueError, IndexError):
                    pass

            if name == "BP_systolic" or (isinstance(value, (int, float)) and confidence == "low"):
                from ..state.models import BloodPressure, Confidence
                bp = BloodPressure(
                    systolic=float(value) if value else None,
                    diastolic=None,
                    timestamp=__import__("datetime").datetime.now(),
                    confidence=Confidence.LOW,
                    requires_confirmation=True,
                    raw_text=obs.get("notes", ""),
                )
                self.store.add_blood_pressure(session_id, bp)
                return {"type": "incomplete_vital", "name": "BP", "confidence": "low"}

        if obs_type == "vital" and name in ("HR", "heart_rate", "pulse"):
            try:
                hr_value = float(value)
                from ..state.models import VitalSign, Confidence
                vital = VitalSign(
                    name="HR",
                    value=hr_value,
                    unit="bpm",
                    timestamp=__import__("datetime").datetime.now(),
                    confidence=Confidence.HIGH if confidence == "high" else Confidence.MEDIUM,
                )
                self.store.add_vital(session_id, vital)
                return {"type": "vital", "name": "HR", "value": hr_value, "confidence": confidence}
            except (ValueError, TypeError):
                pass

        if obs_type == "vital" and name in ("Pain", "pain_level"):
            try:
                pain_value = float(value)
                from ..state.models import VitalSign, Confidence
                vital = VitalSign(
                    name="Pain",
                    value=pain_value,
                    unit="/10",
                    timestamp=__import__("datetime").datetime.now(),
                    confidence=Confidence.HIGH if confidence == "high" else Confidence.MEDIUM,
                )
                self.store.add_vital(session_id, vital)
                return {"type": "vital", "name": "Pain", "value": pain_value, "confidence": confidence}
            except (ValueError, TypeError):
                pass

        if obs_type == "medication":
            from ..state.models import Event, EventType, Confidence
            event = Event(
                id=__import__("uuid").uuid4().hex,
                type=EventType.MEDICATION,
                timestamp=__import__("datetime").datetime.now(),
                data={"name": name, "dose": str(value)},
                raw_text=obs.get("notes", ""),
            )
            self.store.add_medication(session_id, event)
            return {"type": "medication", "name": name, "dose": str(value), "confidence": confidence}

        return None
