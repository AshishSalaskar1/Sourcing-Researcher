---
title: "Supply Risk Radar"
description: "AI-powered supply chain risk analysis prototype using multi-agent orchestration and public data sources"
ms.date: 2026-03-28
---

## Overview

Supply Risk Radar analyzes supply chain risks for food commodities and ingredients using a
multi-agent architecture powered by Pydantic AI and Azure AI Foundry.

## Architecture

```text
┌──────────────────────────────────────────────────┐
│          React + Vite frontend (new)              │
│         sleek dashboard and report viewer         │
└──────────────┬───────────────────────────────────┘
               │ HTTP
               ▼
┌──────────────────────────────────────────────────┐
│               FastAPI backend (new)               │
│     `/api/analyze` wraps the orchestrator         │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│              Orchestrator Agent                   │
│     (coordinates analysis, produces RiskReport)   │
└──────┬───────────────┬───────────────┬───────────┘
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────────┐
│  Sourcing   │ │    Data     │ │   Resilience    │
│   Agent     │ │   Agent     │ │     Agent       │
└──────┬──────┘ └──────┬──────┘ └─────────────────┘
       │               │
       ▼               ▼
┌─────────────┐ ┌────────────────────────────────────┐
│ Commodity   │ │ World Bank · Weather · Public News │
│ Tool        │ │ (data tools)                       │
└─────────────┘ └────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- Azure AI Foundry access with a deployed GPT-4o model

## Setup

```bash
git clone <repo-url> && cd glean-hackathon
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For the frontend:

```bash
cd frontend
npm install
```

Create a `.env` file with your Azure AI Foundry credentials:

```text
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_MODEL=gpt-4o
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Run the split app

```bash
cd backend
python -m uvicorn main:app --reload
```

In another terminal:

```bash
cd frontend
npm run dev
```

The React app defaults to `http://localhost:8000`. Override with:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Legacy Streamlit prototype

The original Streamlit prototype still works and now lives under `backend/` while reusing the shared backend analysis service:

```bash
cd backend
streamlit run streamlit_app.py
```

The `backend/main.py` launcher makes the package imports resolve correctly when you start the backend from inside `backend/`.

## Example Queries

- "What are the supply risks for vanilla?"
- "Analyze cocoa supply chain risks"
- "How vulnerable is palm oil supply?"
- "Assess guar gum supply risks"
- "What could disrupt sunflower oil supply?"

## Data Sources

| Source | Description |
|---|---|
| World Bank | GDP, inflation, and economic indicators |
| Open-Meteo | Historical weather and climate data |
| DuckDuckGo News | Public news coverage for disruptions and current events |
| ND-GAIN | Country climate vulnerability scores |

## Tech Stack

- **Pydantic AI** — Multi-agent orchestration with structured outputs
- **FastAPI** — Backend API for the orchestrator
- **React + Vite** — Frontend application shell
- **Shadcn-style components** — Modern, reusable UI primitives
- **Streamlit** — Legacy prototype UI
- **Azure AI Foundry** — GPT-4o model hosting
- **httpx** — Async HTTP client for tool API calls
