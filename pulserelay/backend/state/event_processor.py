"""Event processor - deterministic vital validation and state transitions."""

import re
import uuid
from datetime import datetime
from typing import Optional

from .models import (
    BloodPressure,
    Confidence,
    Event,
    EventType,
    PatientDemographics,
    VitalSign,
)
from .store import PatientStateStore


class VitalPatterns:
    """Regex patterns for extracting vital signs from text."""

    BP_PATTERN = re.compile(
        r"(?:bp|blood\s*pressure)\s*(?:is\s*|was\s*|now\s*|at\s*)?(\d{1,3})\s*(?:over|/)\s*(\d{1,3})",
        re.IGNORECASE,
    )
    BP_SYSTOLIC_ONLY = re.compile(
        r"(?:bp|blood\s*pressure)\s*(?:is\s*|was\s*|now\s*|at\s*)?(\d{1,3})(?:\s|$|\.|,)",
        re.IGNORECASE,
    )
    BP_NATURAL = re.compile(
        r"(?:pressure|bp)\s*(?:is\s*|was\s*|now\s*|at\s*)?(\d{1,3})\s*(?:over|/)\s*(\d{1,3})",
        re.IGNORECASE,
    )
    BP_NUMBERS_ONLY = re.compile(
        r"^(\d{1,3})\s*(?:over|/)\s*(\d{1,3})\.?$",
        re.IGNORECASE,
    )
    BP_WORD = re.compile(
        r"(?:bp|blood\s*pressure)\s+(?:is\s+|was\s+|now\s+|at\s+)?(\w+(?:[-\s]\w+)?)\s+(?:over|and)\s+(\w+(?:[-\s]\w+)?)",
        re.IGNORECASE,
    )
    BP_WORD_SYSTOLIC = re.compile(
        r"(?:bp|blood\s*pressure)\s+(?:is\s+|was\s+|now\s+|at\s+)?(\w+(?:[-\s]\w+)?)\s*(?:over|\.|\.\.)",
        re.IGNORECASE,
    )
    HR_PATTERN = re.compile(
        r"(?:hr|heart\s*rate|pulse)\s*(?:is\s*|was\s*|now\s*|at\s*)?(\d{2,3})",
        re.IGNORECASE,
    )
    HR_NATURAL = re.compile(
        r"(?:heart|pulse)\s+(?:rate\s+)?(?:is\s+|was\s+|now\s+|at\s+)?(\d{2,3})",
        re.IGNORECASE,
    )
    PAIN_PATTERN = re.compile(
        r"(?:pain|discomfort)\s*(?:is\s*(?:now\s*)?|at\s*|of\s*|rating\s*)?(\d{1,2})\s*(?:out\s*of\s*10|/\s*10)?",
        re.IGNORECASE,
    )
    PAIN_NATURAL = re.compile(
        r"(?:pain|discomfort)\s+(?:is\s+|was\s+|now\s+|at\s+|about\s+|maybe\s+|rating\s+)?(?:a\s+|an\s+)?(\d{1,2})\s*(?:out\s*of\s*10|/\s*10)?",
        re.IGNORECASE,
    )
    PAIN_WORDS = re.compile(
        r"(?:pain|discomfort)\s+(?:is\s+|was\s+|now\s+)?(?:a\s+|an\s+)?(\w+)\s*(?:out\s*of\s*10|/\s*10)?",
        re.IGNORECASE,
    )
    AGE_PATTERN = re.compile(
        r"(\d{1,3})\s*-?\s*(?:year|yr)\s*-?\s*old\b",
        re.IGNORECASE,
    )
    AGE_SEX_PATTERN = re.compile(
        r"(\d{1,3})\s*-?\s*(?:year|yr)\s*-?\s*old\s+(?:male|female|m|f)\b",
        re.IGNORECASE,
    )
    SEX_PATTERN = re.compile(
        r"\b(male|female)\b",
        re.IGNORECASE,
    )
    MEDICATION_PATTERN = re.compile(
        r"(\w[\w\s]*?)\s+(?:administered|given|medicated|delivered)\s*,?\s*(\d+)\s*(mg|mcg|g|ml|units?)",
        re.IGNORECASE,
    )
    MEDICATION_NATURAL = re.compile(
        r"(\w[\w\s]*?)\s+(\d+)\s*(mg|mcg|g|ml|units?)\s+(?:administered|given|medicated|delivered)",
        re.IGNORECASE,
    )
    ASPIRIN_PATTERN = re.compile(
        r"aspirin\s+(?:administered|given|delivered)?\s*,?\s*(\d+)\s*(?:mg|milligrams?)",
        re.IGNORECASE,
    )
    ASPIRIN_NATURAL = re.compile(
        r"aspirin\s+(\d+)\s*(?:mg|milligrams?)\s*(?:administered|given|delivered)?",
        re.IGNORECASE,
    )
    ETA_PATTERN = re.compile(
        r"(?:eta|estimated\s+time|arriving\s+in|two\s+minutes?\s+out|minutes?\s+out)",
        re.IGNORECASE,
    )

    WORD_TO_NUM = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
        "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
        "twentyone": 21, "twenty-one": 21, "twentytwo": 22, "twenty-two": 22,
        "twentythree": 23, "twenty-three": 23, "twentyfour": 24, "twenty-four": 24,
        "twentyfive": 25, "twenty-five": 25, "twentysix": 26, "twenty-six": 26,
        "twentyseven": 27, "twenty-seven": 27, "twentyeight": 28, "twenty-eight": 28,
        "twentynine": 29, "twenty-nine": 29, "thirty": 30,
        "thirtyone": 31, "thirty-one": 31, "thirtytwo": 32, "thirty-two": 32,
        "thirtythree": 33, "thirty-three": 33, "thirtyfour": 34, "thirty-four": 34,
        "thirtyfive": 35, "thirty-five": 35, "thirtysix": 36, "thirty-six": 36,
        "thirtyseven": 37, "thirty-seven": 37, "thirtyeight": 38, "thirty-eight": 38,
        "thirtynine": 39, "thirty-nine": 39, "forty": 40,
        "fortyone": 41, "forty-one": 41, "fortytwo": 42, "forty-two": 42,
        "fortythree": 43, "forty-three": 43, "fortyfour": 44, "forty-four": 44,
        "fortyfive": 45, "forty-five": 45, "fortysix": 46, "forty-six": 46,
        "fortyseven": 47, "forty-seven": 47, "fortyeight": 48, "forty-eight": 48,
        "fortynine": 49, "forty-nine": 49, "fifty": 50,
        "fiftyone": 51, "fifty-one": 51, "fiftytwo": 52, "fifty-two": 52,
        "fiftythree": 53, "fifty-three": 53, "fiftyfour": 54, "fifty-four": 54,
        "fiftyfive": 55, "fifty-five": 55, "fiftysix": 56, "fifty-six": 56,
        "fiftyseven": 57, "fifty-seven": 57, "fiftyeight": 58, "fifty-eight": 58,
        "fiftynine": 59, "fifty-nine": 59, "sixty": 60,
        "sixtyone": 61, "sixty-one": 61, "sixtytwo": 62, "sixty-two": 62,
        "sixtythree": 63, "sixty-three": 63, "sixtyfour": 64, "sixty-four": 64,
        "sixtyfive": 65, "sixty-five": 65, "sixtysix": 66, "sixty-six": 66,
        "sixtyseven": 67, "sixty-seven": 67, "sixtyeight": 68, "sixty-eight": 68,
        "sixtynine": 69, "sixty-nine": 69, "seventy": 70,
        "seventyone": 71, "seventy-one": 71, "seventytwo": 72, "seventy-two": 72,
        "seventythree": 73, "seventy-three": 73, "seventyfour": 74, "seventy-four": 74,
        "seventyfive": 75, "seventy-five": 75, "seventysix": 76, "seventy-six": 76,
        "seventyseven": 77, "seventy-seven": 77, "seventyeight": 78, "seventy-eight": 78,
        "seventynine": 79, "seventy-nine": 79, "eighty": 80,
        "eightyone": 81, "eighty-one": 81, "eightytwo": 82, "eighty-two": 82,
        "eightythree": 83, "eighty-three": 83, "eightyfour": 84, "eighty-four": 84,
        "eightyfive": 85, "eighty-five": 85, "eightysix": 86, "eighty-six": 86,
        "eightyseven": 87, "eighty-seven": 87, "eightyeight": 88, "eighty-eight": 88,
        "eightynine": 89, "eighty-nine": 89, "ninety": 90,
        "ninetyone": 91, "ninety-one": 91, "ninetytwo": 92, "ninety-two": 92,
        "ninetythree": 93, "ninety-three": 93, "ninetyfour": 94, "ninety-four": 94,
        "ninetyfive": 95, "ninety-five": 95, "ninetysix": 96, "ninety-six": 96,
        "ninetyseven": 97, "ninety-seven": 97, "ninetyeight": 98, "ninety-eight": 98,
        "ninetynine": 99, "ninety-nine": 99, "onehundred": 100, "one-hundred": 100,
        "one hundred": 100,
    }

    def word_to_number(self, word: str) -> Optional[float]:
        word = word.lower().strip()
        if word in self.WORD_TO_NUM:
            return float(self.WORD_TO_NUM[word])
        if word.isdigit():
            return float(word)
        return None


class EventProcessor:
    """Processes raw observations into structured events deterministically."""

    def __init__(self, store: PatientStateStore):
        self.store = store
        self.patterns = VitalPatterns()

    def process_observation(self, session_id: str, text: str) -> dict:
        """Process a raw observation text into structured events."""
        results = {
            "events_created": [],
            "warnings": [],
            "pending_items": [],
            "trends": [],
        }

        bp_result = self._extract_bp(session_id, text)
        if bp_result:
            results["events_created"].append(bp_result)

        hr_result = self._extract_hr(session_id, text)
        if hr_result:
            results["events_created"].append(hr_result)

        pain_result = self._extract_pain(session_id, text)
        if pain_result:
            results["events_created"].append(pain_result)

        demo_result = self._extract_demographics(session_id, text)
        if demo_result:
            results["events_created"].append(demo_result)

        med_result = self._extract_medication(session_id, text)
        if med_result:
            results["events_created"].append(med_result)

        complaint_result = self._extract_complaint(session_id, text)
        if complaint_result:
            results["events_created"].append(complaint_result)

        eta_result = self._extract_eta(session_id, text)
        if eta_result:
            results["events_created"].append(eta_result)

        return results

    def _extract_bp(self, session_id: str, text: str) -> Optional[dict]:
        match = self.patterns.BP_PATTERN.search(text)
        if not match:
            match = self.patterns.BP_NATURAL.search(text)
        if not match:
            match = self.patterns.BP_NUMBERS_ONLY.search(text)
        if match:
            systolic = float(match.group(1))
            diastolic = float(match.group(2))

            if not self._validate_bp(systolic, diastolic):
                return {"type": "warning", "message": "BP values out of range", "raw": text}

            bp = BloodPressure(
                systolic=systolic,
                diastolic=diastolic,
                timestamp=datetime.now(),
                confidence=Confidence.HIGH,
                raw_text=text,
            )
            self.store.add_blood_pressure(session_id, bp)
            return {
                "type": "vital",
                "name": "BP",
                "value": f"{systolic}/{diastolic}",
                "confidence": "high",
            }

        word_match = self.patterns.BP_WORD.search(text)
        if word_match:
            systolic = self.patterns.word_to_number(word_match.group(1))
            diastolic = self.patterns.word_to_number(word_match.group(2))
            if systolic is not None and diastolic is not None:
                if self._validate_bp(systolic, diastolic):
                    bp = BloodPressure(
                        systolic=systolic,
                        diastolic=diastolic,
                        timestamp=datetime.now(),
                        confidence=Confidence.HIGH,
                        raw_text=text,
                    )
                    self.store.add_blood_pressure(session_id, bp)
                    return {
                        "type": "vital",
                        "name": "BP",
                        "value": f"{systolic}/{diastolic}",
                        "confidence": "high",
                    }

        word_systolic_match = self.patterns.BP_WORD_SYSTOLIC.search(text)
        if word_systolic_match:
            systolic = self.patterns.word_to_number(word_systolic_match.group(1))
            if systolic is not None and 40 <= systolic <= 300:
                bp = BloodPressure(
                    systolic=systolic,
                    diastolic=None,
                    timestamp=datetime.now(),
                    confidence=Confidence.LOW,
                    requires_confirmation=True,
                    raw_text=text,
                )
                self.store.add_blood_pressure(session_id, bp)
                pending_id = str(uuid.uuid4())
                self.store.add_pending_information(
                    session_id,
                    {
                        "id": pending_id,
                        "type": "bp_diastolic",
                        "message": f"Systolic {systolic} captured but diastolic is missing",
                        "field": "diastolic",
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                return {
                    "type": "incomplete_vital",
                    "name": "BP",
                    "systolic": systolic,
                    "diastolic": None,
                    "confidence": "low",
                    "pending_id": pending_id,
                }

        match = self.patterns.BP_SYSTOLIC_ONLY.search(text)
        if match:
            systolic = float(match.group(1))
            if 40 <= systolic <= 300:
                bp = BloodPressure(
                    systolic=systolic,
                    diastolic=None,
                    timestamp=datetime.now(),
                    confidence=Confidence.LOW,
                    requires_confirmation=True,
                    raw_text=text,
                )
                self.store.add_blood_pressure(session_id, bp)
                pending_id = str(uuid.uuid4())
                self.store.add_pending_information(
                    session_id,
                    {
                        "id": pending_id,
                        "type": "bp_diastolic",
                        "message": f"Systolic {systolic} captured but diastolic is missing",
                        "field": "diastolic",
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                return {
                    "type": "incomplete_vital",
                    "name": "BP",
                    "systolic": systolic,
                    "diastolic": None,
                    "confidence": "low",
                    "pending_id": pending_id,
                }
        return None

    def _validate_bp(self, systolic: float, diastolic: float) -> bool:
        return 40 <= systolic <= 300 and 20 <= diastolic <= 200

    def _extract_hr(self, session_id: str, text: str) -> Optional[dict]:
        match = self.patterns.HR_PATTERN.search(text)
        if not match:
            match = self.patterns.HR_NATURAL.search(text)
        if match:
            hr = float(match.group(1))
            if not (30 <= hr <= 300):
                return {"type": "warning", "message": "HR value out of range", "raw": text}

            vital = VitalSign(
                name="HR",
                value=hr,
                unit="bpm",
                timestamp=datetime.now(),
                confidence=Confidence.HIGH,
                raw_text=text,
            )
            self.store.add_vital(session_id, vital)
            return {"type": "vital", "name": "HR", "value": hr, "confidence": "high"}
        return None

    def _extract_pain(self, session_id: str, text: str) -> Optional[dict]:
        match = self.patterns.PAIN_PATTERN.search(text)
        if not match:
            match = self.patterns.PAIN_NATURAL.search(text)

        if match:
            pain = float(match.group(1))
            if not (0 <= pain <= 10):
                return {"type": "warning", "message": "Pain value out of range", "raw": text}

            vital = VitalSign(
                name="Pain",
                value=pain,
                unit="/10",
                timestamp=datetime.now(),
                confidence=Confidence.HIGH,
                raw_text=text,
            )
            self.store.add_vital(session_id, vital)
            return {"type": "vital", "name": "Pain", "value": pain, "confidence": "high"}

        word_match = self.patterns.PAIN_WORDS.search(text)
        if word_match:
            word_val = word_match.group(1).lower()
            word_to_num = {
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
                "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
            }
            if word_val in word_to_num:
                pain = float(word_to_num[word_val])
                vital = VitalSign(
                    name="Pain",
                    value=pain,
                    unit="/10",
                    timestamp=datetime.now(),
                    confidence=Confidence.HIGH,
                    raw_text=text,
                )
                self.store.add_vital(session_id, vital)
                return {"type": "vital", "name": "Pain", "value": pain, "confidence": "high"}
        return None

    def _extract_demographics(self, session_id: str, text: str) -> Optional[dict]:
        state = self.store.get_or_create_session(session_id)
        changed = False

        age_match = self.patterns.AGE_SEX_PATTERN.search(text)
        if age_match and state.demographics.age is None:
            age = int(age_match.group(1))
            if 1 <= age <= 120:
                state.demographics.age = age
                changed = True

        if not age_match:
            age_match = self.patterns.AGE_PATTERN.search(text)
            if age_match and state.demographics.age is None:
                age = int(age_match.group(1))
                if 1 <= age <= 120:
                    state.demographics.age = age
                    changed = True

        sex_match = self.patterns.SEX_PATTERN.search(text)
        if sex_match and state.demographics.sex is None:
            state.demographics.sex = sex_match.group(1).lower()
            changed = True

        if changed:
            event = Event(
                id=str(uuid.uuid4()),
                type=EventType.DEMOGRAPHIC,
                timestamp=datetime.now(),
                data=state.demographics.to_dict(),
            )
            state.add_event(event)
            return {"type": "demographic", "data": state.demographics.to_dict()}
        return None

    def _extract_medication(self, session_id: str, text: str) -> Optional[dict]:
        aspirin_match = self.patterns.ASPIRIN_PATTERN.search(text)
        if not aspirin_match:
            aspirin_match = self.patterns.ASPIRIN_NATURAL.search(text)
        if aspirin_match:
            dose = aspirin_match.group(1)
            event = Event(
                id=str(uuid.uuid4()),
                type=EventType.MEDICATION,
                timestamp=datetime.now(),
                data={"name": "Aspirin", "dose": f"{dose}mg", "route": "oral"},
                raw_text=text,
            )
            self.store.add_medication(session_id, event)
            return {"type": "medication", "name": "Aspirin", "dose": f"{dose}mg"}

        med_match = self.patterns.MEDICATION_PATTERN.search(text)
        if not med_match:
            med_match = self.patterns.MEDICATION_NATURAL.search(text)
        if med_match:
            name = med_match.group(1).strip()
            dose = f"{med_match.group(2)}{med_match.group(3)}"
            event = Event(
                id=str(uuid.uuid4()),
                type=EventType.MEDICATION,
                timestamp=datetime.now(),
                data={"name": name, "dose": dose},
                raw_text=text,
            )
            self.store.add_medication(session_id, event)
            return {"type": "medication", "name": name, "dose": dose}
        return None

    def _extract_complaint(self, session_id: str, text: str) -> Optional[dict]:
        complaint_keywords = ["chest pain", "shortness of breath", "headache", "abdominal pain", "difficulty breathing"]
        text_lower = text.lower()
        for complaint in complaint_keywords:
            if complaint in text_lower:
                state = self.store.get_or_create_session(session_id)
                if not state.chief_complaint:
                    state.chief_complaint = complaint.title()
                    return {"type": "complaint", "value": complaint.title()}
        return None

    def _extract_eta(self, session_id: str, text: str) -> Optional[dict]:
        if self.patterns.ETA_PATTERN.search(text):
            state = self.store.get_or_create_session(session_id)
            state.is_transport_active = True
            return {"type": "eta", "value": "incoming"}
        return None
