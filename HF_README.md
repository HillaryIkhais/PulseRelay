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

# PulseRelay

Hands-free AI agent for paramedic patient transport documentation.

## Features
- Voice input via browser microphone
- Natural language clinical observation extraction (Gemini 3.5 Flash)
- Real-time vital sign tracking with uncertainty handling
- Proactive trend alerts
- Structured handoff summary generation
- Receiving team dashboard view

## Tech Stack
- **Backend**: Python, FastAPI, Google ADK
- **AI**: Gemini 3.5 Flash (clinical text extraction)
- **Frontend**: Vanilla JS, CSS animations
- **Deployment**: Docker on Hugging Face Spaces
