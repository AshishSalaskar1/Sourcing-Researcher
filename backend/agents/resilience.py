import json
from pathlib import Path

from pydantic_ai import Agent

from backend.agents.models import ResilienceOption

_STRATEGIES_PATH = Path(__file__).resolve().parent.parent / "data" / "resilience_strategies.json"

resilience_agent = Agent(
    output_type=list[ResilienceOption],
    instructions=(
        "You are a supply chain resilience advisor. Given a commodity and its identified risks, "
        "recommend 3-5 practical resilience strategies. Each recommendation must address specific "
        "identified risks. Prioritize strategies by impact and feasibility. "
        "Use the resilience strategy matrix tool to inform your recommendations."
    ),
)


@resilience_agent.tool_plain
def get_resilience_matrix() -> str:
    """Load the resilience strategy matrix with risk-to-strategy mappings."""
    data = json.loads(_STRATEGIES_PATH.read_text())
    return str(data)
