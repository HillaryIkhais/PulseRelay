# PulseRelay — Devpost Submission

## The Problem

Every year, millions of patients are transported by ambulance. During those critical minutes, paramedics are doing two jobs at once: keeping the patient alive *and* trying to document everything the hospital needs to know. They're calling out vitals, administering medications, noting changes — and hoping someone is writing it down correctly.

## The Solution

PulseRelay listens to what the paramedic says, extracts the clinical data in real time, tracks the patient's condition throughout transport, and hands the receiving hospital a complete, structured summary — all without the paramedic ever touching a keyboard.

A paramedic speaks naturally: *"Patient is a 64-year-old male with chest pain. BP 104 over 67, heart rate 108, pain seven out of ten."*

PulseRelay instantly extracts the data, records it, monitors for changes, asks for clarification when something is unclear, and prepares a complete handoff summary.

## Key Features

- **Voice-first input** — Paramedics speak naturally, no structured commands
- **Real-time extraction** — Vital signs, medications, demographics captured instantly
- **Uncertainty handling** — When data is incomplete, it asks instead of guessing
- **Proactive monitoring** — Detects changes and surfaces them without being asked
- **Structured handoff** — Complete transport summary for the receiving hospital
- **Receiving team view** — Real-time dashboard showing transport data as it's captured

## How It Works

1. Paramedic speaks into microphone (or types)
2. Gemini 3.5 Flash extracts structured clinical data
3. Deterministic code validates, stores, and tracks trends
4. Agent detects changes, asks for clarification on incomplete data
5. Handoff summary generated with initial vs. latest vitals, medications, trends

## What Makes This Agentic

- **Autonomous monitoring** — Detects changes without being asked
- **Uncertainty handling** — Asks for clarification when data is incomplete
- **State awareness** — Maintains context across observations
- **Proactive communication** — Surfaces important changes immediately
- **Workflow orchestration** — Manages full transport documentation lifecycle

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Google Gemini 3.5 Flash | Clinical text extraction |
| Google ADK | Agent orchestration |
| FastAPI | Backend API |
| Cloud Run | Application hosting |
| Firestore | Patient state persistence |
| Pub/Sub | Event-driven processing |

## Safety Architecture

Gemini handles language understanding. Deterministic Python code handles everything else — storing values, validating ranges, calculating trends, tracking confidence. No hallucinated vitals. No invented medications. No AI-written clinical notes. The AI understands; the code decides.

## Demo

Run `python demo.py` for a 6-scene walkthrough, or `uvicorn pulserelay.backend.main:app --port 8081` and open the dashboard.

## What It Doesn't Do

PulseRelay does not diagnose. It does not recommend treatment. It does not make medical decisions. It documents what the paramedic observes — accurately, completely, and in real time.

---

*Built for the All Things Agentic Hackathon.*
