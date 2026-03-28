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
│                  Streamlit UI                     │
│              (app.py — chat interface)            │
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
┌─────────────┐ ┌─────────────────────────────────┐
│ Commodity   │ │ World Bank · Weather · ReliefWeb │
│ Tool        │ │ (data tools)                     │
└─────────────┘ └─────────────────────────────────┘
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

Create a `.env` file with your Azure AI Foundry credentials:

```text
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
OPENAI_API_VERSION=2024-12-01-preview
```

## Run

```bash
streamlit run app.py
```

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
| ReliefWeb | Humanitarian alerts and disaster reports |
| ND-GAIN | Country climate vulnerability scores |

## Tech Stack

- **Pydantic AI** — Multi-agent orchestration with structured outputs
- **Streamlit** — Interactive chat UI
- **Azure AI Foundry** — GPT-4o model hosting
- **httpx** — Async HTTP client for tool API calls
