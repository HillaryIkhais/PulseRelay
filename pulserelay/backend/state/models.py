"""Patient state models - deterministic, never LLM-derived."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class EventType(str, Enum):
    VITAL = "vital"
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    INTERVENTION = "intervention"
    ASSESSMENT = "assessment"
    DEMOGRAPHIC = "demographic"


class TrendDirection(str, Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class VitalSign:
    name: str
    value: float
    unit: str
    timestamp: datetime
    confidence: Confidence = Confidence.HIGH
    requires_confirmation: bool = False
    raw_text: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence.value,
            "requires_confirmation": self.requires_confirmation,
            "raw_text": self.raw_text,
        }


@dataclass
class BloodPressure:
    systolic: Optional[float]
    diastolic: Optional[float]
    timestamp: datetime
    confidence: Confidence
    requires_confirmation: bool = False
    raw_text: str = ""

    @property
    def is_complete(self) -> bool:
        return self.systolic is not None and self.diastolic is not None

    def to_dict(self) -> dict:
        return {
            "systolic": self.systolic,
            "diastolic": self.diastolic,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence.value,
            "requires_confirmation": self.requires_confirmation,
            "raw_text": self.raw_text,
            "is_complete": self.is_complete,
        }


@dataclass
class Event:
    id: str
    type: EventType
    timestamp: datetime
    data: dict
    confidence: Confidence = Confidence.HIGH
    requires_confirmation: bool = False
    raw_text: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "confidence": self.confidence.value,
            "requires_confirmation": self.requires_confirmation,
            "raw_text": self.raw_text,
        }


@dataclass
class VitalTrend:
    name: str
    direction: TrendDirection
    values: list[float] = field(default_factory=list)
    timestamps: list[str] = field(default_factory=list)
    delta: float = 0.0
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "direction": self.direction.value,
            "values": self.values,
            "timestamps": self.timestamps,
            "delta": self.delta,
            "message": self.message,
        }


@dataclass
class PatientDemographics:
    age: Optional[int] = None
    sex: Optional[str] = None
    weight: Optional[float] = None
    allergies: list[str] = field(default_factory=list)
    medical_history: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "age": self.age,
            "sex": self.sex,
            "weight": self.weight,
            "allergies": self.allergies,
            "medical_history": self.medical_history,
        }


@dataclass
class PatientState:
    session_id: str
    patient_id: str = ""
    demographics: PatientDemographics = field(default_factory=PatientDemographics)
    chief_complaint: str = ""
    symptoms: list[Event] = field(default_factory=list)
    vitals: list[VitalSign] = field(default_factory=list)
    blood_pressures: list[BloodPressure] = field(default_factory=list)
    heart_rates: list[VitalSign] = field(default_factory=list)
    pain_levels: list[VitalSign] = field(default_factory=list)
    medications: list[Event] = field(default_factory=list)
    interventions: list[Event] = field(default_factory=list)
    assessments: list[Event] = field(default_factory=list)
    timeline: list[Event] = field(default_factory=list)
    pending_information: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_transport_active: bool = True

    @property
    def latest_bp(self) -> Optional[BloodPressure]:
        complete_bps = [bp for bp in self.blood_pressures if bp.is_complete]
        if complete_bps:
            return complete_bps[-1]
        if self.blood_pressures:
            return self.blood_pressures[-1]
        return None

    @property
    def latest_hr(self) -> Optional[VitalSign]:
        return self.heart_rates[-1] if self.heart_rates else None

    @property
    def latest_pain(self) -> Optional[VitalSign]:
        return self.pain_levels[-1] if self.pain_levels else None

    def add_event(self, event: Event):
        self.timeline.append(event)
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "demographics": self.demographics.to_dict(),
            "chief_complaint": self.chief_complaint,
            "latest_bp": self.latest_bp.to_dict() if self.latest_bp else None,
            "latest_hr": self.latest_hr.to_dict() if self.latest_hr else None,
            "latest_pain": self.latest_pain.to_dict() if self.latest_pain else None,
            "vitals": [v.to_dict() for v in self.vitals[-20:]],
            "blood_pressures": [bp.to_dict() for bp in self.blood_pressures[-10:]],
            "medications": [m.to_dict() for m in self.medications],
            "interventions": [i.to_dict() for i in self.interventions],
            "timeline": [e.to_dict() for e in self.timeline[-50:]],
            "pending_information": self.pending_information,
            "alerts": self.alerts,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_transport_active": self.is_transport_active,
        }
