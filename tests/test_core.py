"""Tests for PulseRelay core functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pulserelay.backend.state.models import (
    BloodPressure, VitalSign, Confidence, PatientState
)
from pulserelay.backend.state.store import PatientStateStore
from pulserelay.backend.state.event_processor import EventProcessor
from pulserelay.backend.state.trends import TrendEngine
from pulserelay.backend.safety.rules import SafetyRules
from pulserelay.backend.agent.root_agent import PulseRelayAgent
from datetime import datetime


def test_vital_extraction():
    store = PatientStateStore()
    processor = EventProcessor(store)
    session = store.create_session("test-001")

    results = processor.process_observation("test-001", "BP 104 over 67")
    assert len(results["events_created"]) == 1
    assert results["events_created"][0]["value"] == "104.0/67.0"

    results = processor.process_observation("test-001", "Heart rate 118")
    assert len(results["events_created"]) == 1
    assert results["events_created"][0]["value"] == 118.0

    results = processor.process_observation("test-001", "Pain 7 out of 10")
    assert len(results["events_created"]) == 1
    assert results["events_created"][0]["value"] == 7.0

    print("PASS: test_vital_extraction")


def test_incomplete_bp():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-002", "BP 92")
    assert len(results["events_created"]) == 1
    event = results["events_created"][0]
    assert event["type"] == "incomplete_vital"
    assert event["systolic"] == 92.0
    assert event["diastolic"] is None
    assert event["confidence"] == "low"

    state = store.get_session("test-002")
    assert len(state.pending_information) == 1
    assert state.pending_information[0]["type"] == "bp_diastolic"

    print("PASS: test_incomplete_bp")


def test_medication_extraction():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-003", "Aspirin administered, 324 milligrams")
    assert len(results["events_created"]) == 1
    assert results["events_created"][0]["name"] == "Aspirin"

    state = store.get_session("test-003")
    assert len(state.medications) == 1
    assert state.medications[0].data["name"] == "Aspirin"

    print("PASS: test_medication_extraction")


def test_demographics_extraction():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-004", "Patient is a 64-year-old male with chest pain")
    demographics_event = [e for e in results["events_created"] if e.get("type") == "demographic"]
    assert len(demographics_event) == 1

    state = store.get_session("test-004")
    assert state.demographics.age == 64
    assert state.demographics.sex == "male"
    assert state.chief_complaint == "Chest Pain"

    print("PASS: test_demographics_extraction")


def test_trend_calculation():
    store = PatientStateStore()

    bp1 = BloodPressure(
        systolic=104, diastolic=67,
        timestamp=datetime(2024, 1, 1, 9, 0),
        confidence=Confidence.HIGH
    )
    store.add_blood_pressure("test-005", bp1)

    bp2 = BloodPressure(
        systolic=92, diastolic=58,
        timestamp=datetime(2024, 1, 1, 9, 10),
        confidence=Confidence.HIGH
    )
    store.add_blood_pressure("test-005", bp2)

    state = store.get_session("test-005")
    trend = TrendEngine.calculate_bp_trend(state)

    assert trend is not None
    assert trend.direction.value == "decreasing"
    assert trend.delta == -12.0

    print("PASS: test_trend_calculation")


def test_safety_rules():
    store = PatientStateStore()

    bp1 = BloodPressure(
        systolic=104, diastolic=67,
        timestamp=datetime(2024, 1, 1, 9, 0),
        confidence=Confidence.HIGH
    )
    store.add_blood_pressure("test-006", bp1)

    bp2 = BloodPressure(
        systolic=92, diastolic=58,
        timestamp=datetime(2024, 1, 1, 9, 10),
        confidence=Confidence.HIGH
    )
    store.add_blood_pressure("test-006", bp2)

    state = store.get_session("test-006")
    alerts = SafetyRules.check_vital_trends(state)

    assert len(alerts) == 1
    assert alerts[0]["vital"] == "BP"
    assert alerts[0]["direction"] == "decreasing"

    print("PASS: test_safety_rules")


def test_agent_flow():
    agent = PulseRelayAgent()
    agent.start_session("test-agent-001")

    result = agent.process_observation("test-agent-001", "BP 104 over 67. Heart rate 108.")
    assert result["state"] is not None
    assert result["state"]["latest_bp"]["systolic"] == 104.0

    result = agent.process_observation("test-agent-001", "BP 92")
    assert result["monitoring"]["action"] == "ask"
    assert "diastolic" in result["monitoring"]["message"].lower()

    handoff = agent.get_handoff("test-agent-001")
    assert handoff["patient_info"] is not None
    assert handoff["chief_complaint"] is not None

    handoff_text = agent.get_handoff_text("test-agent-001")
    assert "PATIENT TRANSPORT SUMMARY" in handoff_text
    assert "BP" in handoff_text

    print("PASS: test_agent_flow")


def test_bp_validation():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-007", "BP 350 over 250")
    state = store.get_session("test-007")
    if state and state.blood_pressures:
        bp = state.blood_pressures[0]
        assert bp.confidence == Confidence.LOW
        print("PASS: test_bp_validation (out of range)")
    else:
        print("PASS: test_bp_validation (out of range rejected)")


def test_bp_systolic_only_pending():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-008", "BP 92")
    state = store.get_session("test-008")

    assert len(state.pending_information) == 1
    pending = state.pending_information[0]
    assert pending["type"] == "bp_diastolic"
    assert "92" in pending["message"]

    print("PASS: test_bp_systolic_only_pending")


def test_natural_speech_bp():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-natural-001", "pressure is 120 over 80")
    assert len(results["events_created"]) == 1
    assert results["events_created"][0]["value"] == "120.0/80.0"

    print("PASS: test_natural_speech_bp")


def test_word_numbers_bp():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-word-001", "BP ninety-two over fifty-eight")
    assert len(results["events_created"]) == 1
    event = results["events_created"][0]
    assert event["type"] == "vital"
    assert event["value"] == "92.0/58.0"

    print("PASS: test_word_numbers_bp")


def test_incomplete_bp_word_number():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-word-002", "BP ninety-two over...")
    assert len(results["events_created"]) == 1
    event = results["events_created"][0]
    assert event["type"] == "incomplete_vital"
    assert event["systolic"] == 92.0
    assert event["diastolic"] is None
    assert event["confidence"] == "low"

    state = store.get_session("test-word-002")
    assert len(state.pending_information) == 1
    assert state.pending_information[0]["type"] == "bp_diastolic"

    print("PASS: test_incomplete_bp_word_number")


def test_natural_speech_hr():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-natural-002", "heart rate is 118")
    assert len(results["events_created"]) == 1
    assert results["events_created"][0]["value"] == 118.0

    print("PASS: test_natural_speech_hr")


def test_word_numbers_pain():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-word-003", "pain is seven out of ten")
    assert len(results["events_created"]) == 1
    event = results["events_created"][0]
    assert event["type"] == "vital"
    assert event["value"] == 7.0

    print("PASS: test_word_numbers_pain")


def test_natural_medication():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-med-001", "aspirin 324 mg given")
    assert len(results["events_created"]) == 1
    event = results["events_created"][0]
    assert event["type"] == "medication"
    assert event["name"] == "Aspirin"
    assert event["dose"] == "324mg"

    print("PASS: test_natural_medication")


def test_eta_detection():
    store = PatientStateStore()
    processor = EventProcessor(store)

    results = processor.process_observation("test-eta-001", "We're two minutes out")
    state = store.get_session("test-eta-001")
    assert state.is_transport_active == True

    eta_events = [e for e in results["events_created"] if e.get("type") == "eta"]
    assert len(eta_events) == 1

    print("PASS: test_eta_detection")


def test_full_demo_scenario():
    agent = PulseRelayAgent()
    session = "test-full-demo"
    agent.start_session(session)

    result = agent.process_observation(session, "Patient is a 64-year-old male with chest pain. BP 104 over 67. Heart rate 108. Pain seven out of ten.")
    assert result["state"]["latest_bp"]["systolic"] == 104.0
    assert result["state"]["chief_complaint"] == "Chest Pain"

    result = agent.process_observation(session, "Aspirin 324 milligrams administered.")
    assert len(result["state"]["medications"]) == 1

    result = agent.process_observation(session, "BP 98 over 61. Heart rate 116. Pain is now eight.")
    assert result["monitoring"]["action"] == "alert"

    result = agent.process_observation(session, "BP ninety-two over...")
    assert result["monitoring"]["action"] == "ask"
    assert "diastolic" in result["monitoring"]["message"].lower()

    result = agent.process_observation(session, "92 over 58.")
    assert result["state"]["latest_bp"]["systolic"] == 92.0
    assert result["state"]["latest_bp"]["diastolic"] == 58.0

    result = agent.process_observation(session, "We're two minutes out.")
    handoff = agent.get_handoff_text(session)
    assert "64M" in handoff
    assert "Aspirin" in handoff

    print("PASS: test_full_demo_scenario")


if __name__ == "__main__":
    test_vital_extraction()
    test_incomplete_bp()
    test_medication_extraction()
    test_demographics_extraction()
    test_trend_calculation()
    test_safety_rules()
    test_agent_flow()
    test_bp_validation()
    test_bp_systolic_only_pending()
    test_natural_speech_bp()
    test_word_numbers_bp()
    test_incomplete_bp_word_number()
    test_natural_speech_hr()
    test_word_numbers_pain()
    test_natural_medication()
    test_eta_detection()
    test_full_demo_scenario()
    print("\nAll tests passed!")
