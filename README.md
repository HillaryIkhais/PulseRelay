# PulseRelay

**Hands-free AI agent for paramedic patient transport**

PulseRelay listens to paramedic observations during ambulance transport, converts them into structured clinical events, maintains a deterministic live patient state, detects changes and missing information, asks for clarification when uncertain, proactively surfaces important state changes, and prepares a structured handoff for the receiving hospital.

## Architecture

```
                  PARAMEDIC
                      │
                      │ voice/text
                      ▼
              ┌───────────────┐
              │ Audio / Input │
              └───────┬───────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Gemini (ADK)    │
             │ extraction      │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Event Validator │
             │ + confidence    │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Patient State   │
             │ Store           │
             └────────┬────────┘
                      │
              ┌───────┴────────┐
              ▼                ▼
       Trend Engine       Completeness
              │                │
              └───────┬────────┘
                      ▼
             ┌─────────────────┐
             │ Agent Decision  │
             └────────┬────────┘
                      │
             ┌────────┴─────────┐
             ▼                  ▼
       Ask paramedic       Proactive alert
             │                  │
             └────────┬─────────┘
                      ▼
             ┌─────────────────┐
             │ Handoff Agent   │
             └────────┬────────┘
                      ▼
              Receiving Hospital
```

## Safety Architecture

**Critical design decision**: Gemini is NOT the source of truth for clinical state.

| Component | Responsibility |
|-----------|---------------|
| **Gemini (ADK)** | Natural language understanding, extraction, clarification, reasoning over state |
| **Deterministic Code** | Storing patient state, validating vital-sign formats, timestamps, calculating trends, detecting missing values, confidence handling, state transitions |

This separation ensures:
- No hallucinated clinical values
- Deterministic trend calculations
- Reliable confidence tracking
- Audit-safe state management

## Tech Stack

- **Python** - Backend language
- **FastAPI** - REST API framework
- **Google ADK** - Agent orchestration framework
- **Google Gemini** - Natural language extraction (via ADK)
- **Cloud Run** - Serverless deployment
- **Firestore** - Patient/session state persistence
- **Pub/Sub** - Event-driven observation processing

## GCP Services Used

| Service | Purpose |
|---------|---------|
| **Cloud Run** | Hosts the application API and frontend |
| **Firestore** | Persists patient state and session data |
| **Pub/Sub** | Event-driven observation processing pipeline |
| **Vertex AI/Gemini** | Clinical text extraction via ADK |
| **Cloud Build** | Builds Docker images for deployment |

## Project Structure

```
pulserelay/
├── backend/
│   ├── agent/          # Agent orchestration
│   │   ├── root_agent.py
│   │   ├── extraction_agent.py
│   │   ├── monitoring_agent.py
│   │   ├── handoff_agent.py
│   │   └── adk_agent.py      # ADK integration
│   ├── state/          # Deterministic state management
│   │   ├── models.py
│   │   ├── store.py           # In-memory store (local)
│   │   ├── firestore_store.py # Firestore store (cloud)
│   │   ├── event_processor.py
│   │   └── trends.py
│   ├── safety/         # Validation and confidence
│   │   ├── validation.py
│   │   ├── confidence.py
│   │   └── rules.py
│   ├── api/            # REST endpoints
│   │   └── routes.py
│   ├── config.py       # Environment configuration
│   ├── pubsub.py       # Pub/Sub integration
│   └── main.py
├── frontend/           # Operational dashboard
│   └── index.html
├── tests/              # Test suite
│   └── test_core.py
├── infrastructure/     # Cloud deployment
│   └── cloudrun/
├── demo.py             # Demo simulation
├── deploy.sh           # Deployment script
├── Dockerfile
└── requirements.txt
```

## Quick Start (Local)

```bash
# Install dependencies
pip install -r requirements.txt

# Run demo simulation
python demo.py

# Start server
uvicorn pulserelay.backend.main:app --host 0.0.0.0 --port 8081

# Open dashboard
open http://localhost:8081
```

## Deployment to Google Cloud

### Prerequisites

1. Google Cloud account with billing enabled
2. GCP project ID (e.g., `pulserelay-506715`)
3. Docker installed locally
4. gcloud CLI installed and authenticated

### One-Command Deployment

```bash
# Authenticate with GCP
gcloud auth login

# Set project
gcloud config set project pulserelay-506715

# Run deployment script
./deploy.sh
```

### Manual Deployment

```bash
# 1. Enable required APIs
gcloud services enable run.googleapis.com firestore.googleapis.com pubsub.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# 2. Create Firestore database
gcloud firestore databases create --location=us-central1

# 3. Create Pub/Sub resources
gcloud pubsub topics create pulse-observations
gcloud pubsub subscriptions create pulse-observations-sub --topic=pulse-observations

# 4. Build and push Docker image
docker build -t gcr.io/pulserelay-506715/pulserelay:latest .
docker push gcr.io/pulserelay-506715/pulserelay:latest

# 5. Deploy to Cloud Run
gcloud run deploy pulserelay \
    --image=gcr.io/pulserelay-506715/pulserelay:latest \
    --region=us-central1 \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=pulserelay-506715"
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | `development` or `production` | `development` |
| `GCP_PROJECT_ID` | Google Cloud project ID | `pulserelay-506715` |
| `GEMINI_MODEL` | Gemini model to use | `gemini-3.5-flash` |
| `GEMINI_API_KEY` | Gemini API key (if not using ADC) | - |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check for Cloud Run |
| `/api/session/start` | POST | Start new patient session |
| `/api/observe` | POST | Submit observation text |
| `/api/state/{session_id}` | GET | Get current patient state |
| `/api/trends/{session_id}` | GET | Get vital sign trends |
| `/api/handoff/{session_id}` | GET | Generate handoff summary |
| `/api/handoff/{session_id}/text` | GET | Get formatted handoff text |

## Firestore Schema

**Collection: `sessions`**
```
{
  "session_id": "string",
  "patient_id": "string",
  "demographics": {
    "age": "number",
    "sex": "string",
    "weight": "number",
    "allergies": ["string"],
    "medical_history": ["string"]
  },
  "chief_complaint": "string",
  "vitals": [...],
  "blood_pressures": [...],
  "heart_rates": [...],
  "pain_levels": [...],
  "medications": [...],
  "interventions": [...],
  "timeline": [...],
  "pending_information": [...],
  "alerts": [...],
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "is_transport_active": "boolean"
}
```

## Pub/Sub Configuration

**Topic: `pulse-observations`**
- Receives observation events from the API
- Message format: `{session_id, text, extraction_result, timestamp}`

**Subscription: `pulse-observations-sub`**
- Ack deadline: 60 seconds
- Processes observations asynchronously

## Demo Scenario

A 64-year-old male transported for chest pain:

1. **Scene 1**: Initial assessment - BP 104/67, HR 108, Pain 7/10
2. **Scene 2**: Aspirin 324mg administered
3. **Scene 3**: Condition changes - BP 98/61, HR 116, Pain 8/10
4. **Scene 4**: Incomplete BP reading - system asks for clarification
5. **Scene 5**: Clarification provided - BP 92/58
6. **Scene 6**: Handoff request - transport summary generated

## Features

- **Voice input** - Browser microphone with Web Speech API
- **Natural language extraction** - Supports paramedic speech patterns
- **Word number support** - "ninety-two", "seventeen", etc.
- **Deterministic state management** - Never relies on LLM for clinical values
- **Incomplete data handling** - Asks for clarification when observations are partial
- **Trend detection** - Identifies significant vital sign changes
- **Proactive alerts** - Surfaces important state changes without diagnosis
- **Receiving team view** - Second dashboard for hospital staff
- **Structured handoff** - Generates complete transport summary

## Testing

```bash
# Run all tests
python tests/test_core.py

# Run demo
python demo.py
```

## License

MIT
