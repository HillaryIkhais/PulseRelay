# PulseRelay - Devpost Submission

## Track: Taskmaster

## One-liner
Hands-free AI agent that lets paramedics document patient transport by speaking naturally, while automatically detecting clinical changes and preparing hospital handoffs.

## The Problem
During ambulance transport, paramedics are busy treating patients. They shouldn't have to stop care to type into a computer. Yet patient records must be accurate, complete, and available to the receiving hospital.

## The Solution
PulseRelay listens to paramedic observations, extracts structured clinical data, maintains a live patient state, detects changes and missing information, and prepares a structured handoff - all without requiring the paramedic to touch a keyboard.

## Key Features

### 1. Natural Voice Input
Paramedics speak naturally - no structured commands needed.
- "BP is 104 over 67, heart rate 108, pain is about a seven"
- "Aspirin 324 milligrams given"
- "Pressure is 98 over 61 now, heart rate 116, pain is worse, maybe an eight"

### 2. Uncertainty Handling (Strong Demo Moment)
When observations are incomplete, PulseRelay asks for clarification - never invents values.
- Input: "BP ninety-two over..."
- Response: "I captured systolic 92, but the diastolic value is unclear. Can you repeat it?"

### 3. Proactive State Monitoring
The agent surfaces meaningful changes without being asked.
- "Patient state is changing: BP decreased from 104/67 to 92/58 while heart rate increased from 108 to 116."

### 4. Deterministic State Engine
Clinical state is managed by deterministic code, not the LLM.
- Gemini handles: natural language extraction, reasoning, conversation
- Code handles: state storage, trend calculation, validation, confidence

### 5. Structured Handoff
Generates complete transport summary for receiving hospital:
- Patient demographics and chief complaint
- Initial vs. latest vitals
- Medications administered
- Trend analysis
- Timeline of events
- Items requiring clinician review

### 6. Receiving Team View
Real-time dashboard showing transport data as it's captured.

## Architecture

```
Paramedic Speech → Gemini (ADK) → Event Validator → Patient State Store
                                                          ↓
                                        ┌─────────────────┴─────────────────┐
                                        ↓                                   ↓
                                  Trend Engine                      Completeness Check
                                        ↓                                   ↓
                                        └─────────────────┬─────────────────┘
                                                          ↓
                                                    Agent Decision
                                                          ↓
                                              ┌───────────┴───────────┐
                                              ↓                       ↓
                                      Ask Paramedic          Proactive Alert
                                              ↓                       ↓
                                              └───────────┬───────────┘
                                                          ↓
                                                    Handoff Agent
                                                          ↓
                                                  Receiving Hospital
```

## Google Stack

| Service | Purpose |
|---------|---------|
| **Google ADK** | Agent orchestration framework |
| **Gemini 3.5 Flash** | Clinical text extraction |
| **Cloud Run** | Application hosting |
| **Firestore** | Patient state persistence |
| **Pub/Sub** | Event-driven processing |

## Demo Scenario

**Patient**: 64-year-old male with chest pain during ambulance transport.

| Scene | Paramedic Says | System Response |
|-------|---------------|-----------------|
| 1 | "BP 104 over 67, HR 108, pain 7/10" | Records vitals, extracts demographics |
| 2 | "Aspirin 324mg administered" | Records medication |
| 3 | "BP 98 over 61, HR 116, pain 8" | Detects changes, sends alert |
| 4 | "BP ninety-two over..." | Asks for clarification (uncertainty) |
| 5 | "92 over 58" | Updates state, calculates trends |
| 6 | "Two minutes out" | Generates handoff summary |

## What Makes This Agentic

1. **Autonomous monitoring** - Detects changes without being asked
2. **Uncertainty handling** - Asks for clarification when data is incomplete
3. **State awareness** - Maintains context across observations
4. **Proactive communication** - Surfaces important changes immediately
5. **Workflow orchestration** - Manages full transport documentation lifecycle

## What We Did NOT Build (By Design)

- No medical diagnosis
- No treatment recommendations
- No autonomous medical decisions
- No fake clinical validation
- No unnecessary complexity

## Running the Demo

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI demo
python demo.py

# Run web dashboard
uvicorn pulserelay.backend.main:app --port 8081
# Open http://localhost:8081
```

## Team

Built for the All Things Agentic Hackathon.

## License

MIT
