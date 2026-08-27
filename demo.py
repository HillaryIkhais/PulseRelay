"""Demo simulation - runs the full transport scenario."""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pulserelay.backend.agent.root_agent import PulseRelayAgent


def run_demo():
    agent = PulseRelayAgent()
    session_id = "demo-session-001"
    agent.start_session(session_id)

    scenes = [
        {
            "name": "Scene 1 - Transport Begins",
            "input": "Patient is a 64-year-old male with chest pain. BP 104 over 67. Heart rate 108. Pain seven out of ten.",
        },
        {
            "name": "Scene 2 - Treatment",
            "input": "Aspirin 324 milligrams administered.",
        },
        {
            "name": "Scene 3 - Condition Changes",
            "input": "BP 98 over 61. Heart rate 116. Pain is now eight.",
        },
        {
            "name": "Scene 4 - Missing Information",
            "input": "BP ninety-two over...",
        },
        {
            "name": "Scene 5 - Clarification",
            "input": "92 over 58.",
        },
        {
            "name": "Scene 6 - Handoff Request",
            "input": "We're two minutes out.",
        },
    ]

    for scene in scenes:
        print(f"\n{'='*60}")
        print(f"  {scene['name']}")
        print(f"{'='*60}")
        print(f"\n  Paramedic: \"{scene['input']}\"")

        result = agent.process_observation(session_id, scene["input"])

        monitoring = result["monitoring"]
        print(f"\n  Agent: {monitoring['message']}")

        if monitoring.get("alerts"):
            for alert in monitoring["alerts"]:
                print(f"  Alert: {alert['message']}")

        state = result["state"]
        if state:
            print(f"\n  State:")
            if state.get("latest_bp"):
                bp = state["latest_bp"]
                if bp.get("is_complete"):
                    print(f"    BP: {bp['systolic']}/{bp['diastolic']}")
                else:
                    print(f"    BP: {bp['systolic']}/? (incomplete)")
            if state.get("latest_hr"):
                print(f"    HR: {state['latest_hr']['value']}")
            if state.get("latest_pain"):
                print(f"    Pain: {state['latest_pain']['value']}/10")
            if state.get("chief_complaint"):
                print(f"    Complaint: {state['chief_complaint']}")

    print(f"\n{'='*60}")
    print("  HANDOFF SUMMARY")
    print(f"{'='*60}")
    handoff_text = agent.get_handoff_text(session_id)
    print(handoff_text)

    print(f"\n{'='*60}")
    print("  DEMO COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_demo()
