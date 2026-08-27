# PulseRelay Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PULSERELAY SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐                                                          │
│  │   PARAMEDIC  │                                                          │
│  │   (Voice/    │                                                          │
│  │    Text)     │                                                          │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         │ speech/text                                                       │
│         ▼                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        INPUT LAYER                                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │  │
│  │  │   Browser   │  │    REST     │  │   Voice     │                  │  │
│  │  │  Microphone │  │    API      │  │   Input     │                  │  │
│  │  │  (Web API)  │  │  /observe   │  │  (Future)   │                  │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │  │
│  │         │                │                │                          │  │
│  │         └────────────────┼────────────────┘                          │  │
│  │                          │                                            │  │
│  └──────────────────────────┼───────────────────────────────────────────┘  │
│                             │                                               │
│                             ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     AGENT LAYER (ADK)                                 │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │                    Gemini 3.5 Flash                             │ │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │ │  │
│  │  │  │  Extraction │  │  Reasoning  │  │   Safety    │            │ │  │
│  │  │  │   Agent     │  │   Engine    │  │   Layer     │            │ │  │
│  │  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │ │  │
│  │  │         │                │                │                     │ │  │
│  │  └─────────┼────────────────┼────────────────┼─────────────────────┘ │  │
│  │            │                │                │                        │  │
│  │            ▼                ▼                ▼                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │              Deterministic State Engine                         │ │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │ │  │
│  │  │  │   Event     │  │   Trend     │  │  Confidence │            │ │  │
│  │  │  │ Processor   │  │   Engine    │  │  Calculator │            │ │  │
│  │  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │ │  │
│  │  └─────────┼────────────────┼────────────────┼─────────────────────┘ │  │
│  └────────────┼────────────────┼────────────────┼────────────────────────┘  │
│               │                │                │                           │
│               ▼                ▼                ▼                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      STATE LAYER                                      │  │
│  │                                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │  │
│  │  │  In-Memory  │  │  Firestore  │  │    Pub/Sub  │                  │  │
│  │  │   Store     │  │   (Cloud)   │  │   Events    │                  │  │
│  │  │  (Local)    │  │             │  │             │                  │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │  │
│  │         │                │                │                          │  │
│  │         └────────────────┼────────────────┘                          │  │
│  │                          │                                            │  │
│  └──────────────────────────┼───────────────────────────────────────────┘  │
│                             │                                               │
│                             ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      OUTPUT LAYER                                     │  │
│  │                                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │  │
│  │  │  Proactive  │  │  Handoff    │  │  Receiving  │                  │  │
│  │  │   Alerts    │  │  Summary    │  │    Team     │                  │  │
│  │  │             │  │             │  │    View     │                  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │  │
│  │                                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OBSERVATION FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  "BP 92 over..."                                                           │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────┐                                                           │
│  │   Gemini    │ ← Extracts: BP systolic = 92                              │
│  │  (ADK)      │   Detects: diastolic missing                              │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐                                                           │
│  │  Validator  │ ← Validates: systolic in range (40-300)                   │
│  │             │   Flags: confidence = LOW                                  │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐                                                           │
│  │   State     │ ← Stores: BP = 92/? (incomplete)                         │
│  │   Store     │   Adds: pending_information item                          │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐                                                           │
│  │   Agent     │ ← Evaluates: incomplete vital detected                    │
│  │  Decision   │   Action: ASK for clarification                          │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  "I captured systolic 92, but the diastolic value is unclear.              │
│   Can you repeat the full blood pressure?"                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Input Layer
- **Browser Microphone**: Web Speech API for voice input
- **REST API**: `/api/observe` endpoint for text input
- **Natural Language**: Supports paramedic speech patterns

### 2. Agent Layer (Google ADK)
- **Gemini 2.0 Flash**: Clinical text extraction
- **Extraction Agent**: Parses vital signs, medications, demographics
- **Safety Layer**: Validates values, detects incomplete data

### 3. Deterministic State Engine
- **Event Processor**: Regex + validation for vital signs
- **Trend Engine**: Calculates BP, HR, pain changes
- **Confidence Calculator**: Tracks data certainty

### 4. State Layer
- **In-Memory Store**: Local development
- **Firestore**: Cloud persistence (when billing enabled)
- **Pub/Sub**: Event-driven processing (when billing enabled)

### 5. Output Layer
- **Proactive Alerts**: Surfaces significant changes
- **Handoff Summary**: Structured transport documentation
- **Receiving Team View**: Real-time hospital dashboard

## GCP Integration Points

| Component | Google Service | Status |
|-----------|---------------|--------|
| Agent Orchestration | Google ADK | Ready |
| Text Extraction | Gemini 2.0 Flash | Ready |
| State Persistence | Firestore | Code written, needs billing |
| Event Processing | Pub/Sub | Code written, needs billing |
| Deployment | Cloud Run | Config ready, needs billing |

## Safety Architecture

**Critical**: Gemini is NEVER the source of truth for clinical state.

```
Gemini (LLM)          Deterministic Code
     │                        │
     │ extracts               │ validates
     │                        │
     ▼                        ▼
┌─────────┐            ┌─────────┐
│ "BP 92" │ ────────►  │ BP: 92/?│
│         │            │ conf: LOW│
└─────────┘            │ pending: TRUE│
                       └─────────┘
```

This ensures:
- No hallucinated clinical values
- Deterministic trend calculations
- Reliable confidence tracking
- Audit-safe state management
