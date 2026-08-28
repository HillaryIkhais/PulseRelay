---
title: PulseRelay
emoji: 🏥
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# PulseRelay — Clinical Transport Intelligence

## What It Does

Paramedics speak. PulseRelay listens, extracts structured clinical data, tracks patient state across transport, detects changes, catches incomplete observations, and hands the receiving hospital a complete summary.

**The core insight:** Paramedics shouldn't have to choose between treating the patient and documenting the patient.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PARAMEDIC INPUT                              │
│                  (Voice / Text / Browser)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GEMINI 3.5 FLASH                              │
│              Clinical Text Extraction (ADK)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Vital Signs │  │ Medications │  │ Demographics │             │
│  │  BP, HR,    │  │  Name,      │  │  Age, Sex,   │             │
│  │  Pain       │  │  Dose       │  │  Complaint   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                DETERMINISTIC STATE ENGINE                        │
│         (Never relies on LLM for clinical values)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Event     │  │   Trend     │  │ Confidence  │             │
│  │  Processor  │  │   Engine    │  │  Calculator │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AGENT DECISION LAYER                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Monitoring │  │  Handoff    │  │  Safety     │             │
│  │   Agent     │  │   Agent     │  │   Rules     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Proactive│ │  Ask for │ │ Handoff  │
        │  Alert    │ │  Clarify │ │ Summary  │
        └──────────┘ └──────────┘ └──────────┘
```

## Google Cloud Integration

| Service | Purpose | Status |
|---------|---------|--------|
| **Gemini 3.5 Flash** | Clinical text extraction | ✅ Active |
| **Google ADK** | Agent orchestration | ✅ Active |
| **Cloud Run** | Application hosting | ✅ Configured |
| **Firestore** | Patient state persistence | ✅ Code ready |
| **Pub/Sub** | Event-driven processing | ✅ Code ready |

## Key Design Decision

**Gemini is NOT the source of truth for clinical state.**

- Gemini handles: natural language understanding, extraction, conversation
- Deterministic code handles: state storage, validation, trend calculation, confidence tracking

This ensures no hallucinated clinical values, deterministic trend calculations, and audit-safe state management.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn pulserelay.backend.main:app --port 8081
# Open http://localhost:8081
```

## Tech Stack

- Python, FastAPI, Google ADK, Gemini 3.5 Flash
- Cloud Run, Firestore, Pub/Sub (Google Cloud)
- Web Speech API (browser voice input)
- 17 passing tests

## Demo

Click buttons 1–6 to walk through a complete patient transport scenario:

1. Initial assessment (vitals + demographics)
2. Medication administration
3. Condition change (proactive alert)
4. Incomplete observation (asks for clarification)
5. Clarification provided (trend detection)
6. Handoff summary generated
