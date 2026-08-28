# PulseRelay

**Paramedics talk. PulseRelay listens, remembers, and hands it off.**

---

Every year, millions of patients are transported by ambulance. During those critical minutes, paramedics are doing two jobs at once: keeping the patient alive *and* trying to document everything the hospital needs to know. They're calling out vitals, administering medications, noting changes — and hoping someone is writing it down correctly.

PulseRelay changes that. It listens to what the paramedic says, extracts the clinical data in real time, tracks the patient's condition throughout transport, and hands the receiving hospital a complete, structured summary — all without the paramedic ever touching a keyboard.

## What It Does

A paramedic speaks naturally into a microphone:

> "Patient is a 64-year-old male with chest pain. BP 104 over 67, heart rate 108, pain seven out of ten."

PulseRelay instantly:

1. **Extracts** the structured data: age 64, male, chest pain, BP 104/67, HR 108, pain 7/10
2. **Records** it with timestamps and confidence levels
3. **Monitors** for changes — if blood pressure drops or heart rate spikes, it alerts
4. **Asks** when something is unclear: "BP ninety-two over..." → *"I captured systolic 92, but the diastolic is unclear. Can you repeat?"*
5. **Prepares** a complete handoff summary for the receiving hospital

No buttons. No screens. Just talk.

## Why It Matters

In an ambulance, seconds count. Every moment a paramedic spends typing into a computer is a moment they're not watching the patient. PulseRelay lets them stay focused on care while building an accurate, complete clinical record in the background.

When they arrive at the hospital, instead of fumbling through handwritten notes, they hand over a structured summary: initial vs. latest vitals, medications given, trend analysis, and anything that needs clinician review.

## How It Works

```
Paramedic speaks
       ↓
  Gemini 3.5 Flash extracts clinical data
       ↓
  Deterministic code validates & stores
       ↓
  Agent detects trends, asks for clarification
       ↓
  Handoff summary generated for hospital
```

**The critical design choice**: Gemini handles understanding language. Deterministic Python code handles everything else — storing values, validating ranges, calculating trends, tracking confidence. This means no hallucinated vitals, no invented medications, no AI-written clinical notes. The AI understands; the code decides.

## Demo Walkthrough

A 64-year-old male with chest pain during transport:

| Scene | Paramedic Says | PulseRelay Does |
|-------|---------------|-----------------|
| 1 | "BP 104 over 67, HR 108, pain 7" | Records initial vitals and demographics |
| 2 | "Aspirin 324mg given" | Logs medication with timestamp |
| 3 | "BP 98 over 61, HR 116, pain 8" | Detects changes, sends proactive alert |
| 4 | "BP ninety-two over..." | Asks for clarification (incomplete data) |
| 5 | "92 over 58" | Updates state, calculates trends |
| 6 | "Two minutes out" | Generates complete handoff summary |

## Run It

```bash
pip install -r requirements.txt
uvicorn pulserelay.backend.main:app --port 8081
# Open http://localhost:8081
```

Click buttons 1–6 to walk through the full scenario. Or press the mic button and speak naturally.

## Built With

- **Google Gemini 3.5 Flash** — Clinical text extraction
- **Google ADK** — Agent orchestration
- **FastAPI** — Backend API
- **Cloud Run / Firestore / Pub/Sub** — Google Cloud infrastructure

## What It Doesn't Do

PulseRelay does not diagnose. It does not recommend treatment. It does not make medical decisions. It documents what the paramedic observes and says — accurately, completely, and in real time. Clinical decisions remain with clinicians.

---

*Built for the All Things Agentic Hackathon. MIT License.*
