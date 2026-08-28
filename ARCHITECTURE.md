# PulseRelay Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PULSERELAY                                │
│            Clinical Transport Intelligence System                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    INPUT LAYER                            │   │
│  │  Browser Microphone (Web Speech API)  │  REST API         │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │                 AGENT LAYER (ADK)                         │   │
│  │  ┌─────────────────────────────────────────────────┐     │   │
│  │  │           Gemini 3.5 Flash                       │     │   │
│  │  │  Extract: Vitals, Medications, Demographics      │     │   │
│  │  └─────────────────────────────────────────────────┘     │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │              DETERMINISTIC STATE ENGINE                    │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │  Event   │  │  Trend   │  │Confidence│               │   │
│  │  │Processor │  │  Engine  │  │Calculator│               │   │
│  │  └──────────┘  └──────────┘  └──────────┘               │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │                   STATE LAYER                             │   │
│  │  In-Memory Store │ Firestore (Cloud) │ Pub/Sub Events    │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │                  OUTPUT LAYER                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │Proactive │  │  Ask for │  │ Handoff  │               │   │
│  │  │  Alert   │  │Clarify   │  │ Summary  │               │   │
│  │  └──────────┘  └──────────┘  └──────────┘               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Paramedic: "BP ninety-two over..."
         │
         ▼
    Gemini 3.5 Flash
    Extracts: BP systolic = 92
    Detects: diastolic missing
         │
         ▼
    Validator
    Flags: confidence = LOW
    Triggers: ask_for_clarification
         │
         ▼
    Agent Decision
    Action: ASK
    Message: "I captured systolic 92, but the diastolic
              is unclear. Can you repeat?"
         │
         ▼
    Banner appears in UI (yellow)
```

## Safety Architecture

**Critical**: Gemini is NEVER the source of truth for clinical state.

```
Gemini (LLM)              Deterministic Code
     │                          │
     │ extracts                 │ validates
     │                          │
     ▼                          ▼
┌─────────┐              ┌─────────┐
│ "BP 92" │ ──────────►  │ BP: 92/?│
│         │              │ conf: LOW│
└─────────┘              │ pending:│
                         │  TRUE   │
                         └─────────┘
```

## Google Cloud Services

| Service | Role | Implementation |
|---------|------|----------------|
| **Gemini 3.5 Flash** | Clinical text extraction | `extraction_agent.py` via ADK |
| **Google ADK** | Agent orchestration | `adk_agent.py` — LlmAgent + FunctionTool |
| **Cloud Run** | Application hosting | `Dockerfile` + `infrastructure/cloudrun/service.yaml` |
| **Firestore** | Patient state persistence | `state/firestore_store.py` |
| **Pub/Sub** | Event-driven processing | `pubsub.py` |

## Project Structure

```
pulserelay/
├── backend/
│   ├── agent/              # Agent orchestration
│   │   ├── root_agent.py       # Main coordinator
│   │   ├── extraction_agent.py # Gemini extraction
│   │   ├── monitoring_agent.py # Proactive alerts
│   │   ├── handoff_agent.py    # Summary generation
│   │   └── adk_agent.py        # ADK integration
│   ├── state/              # Deterministic state
│   │   ├── models.py           # PatientState dataclass
│   │   ├── store.py            # In-memory store
│   │   ├── firestore_store.py  # Firestore store
│   │   ├── event_processor.py  # Regex + validation
│   │   └── trends.py           # Trend calculation
│   ├── safety/             # Validation
│   │   ├── rules.py            # Safety rules
│   │   ├── validation.py       # Vital validation
│   │   └── confidence.py       # Confidence calc
│   ├── api/routes.py       # REST endpoints
│   ├── config.py           # Environment config
│   ├── pubsub.py           # Pub/Sub integration
│   └── main.py             # FastAPI app
├── frontend/index.html     # Dashboard UI
├── tests/test_core.py      # 17 passing tests
├── Dockerfile              # Container config
├── deploy.sh               # GCP deployment
└── requirements.txt        # Dependencies
```
