from dataclasses import dataclass

import httpx
from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

from agents.models import SourcingAnalysis
from tools.commodity import lookup_commodity_profile


@dataclass
class SourcingDeps:
    http_client: httpx.AsyncClient


sourcing_agent = Agent(
    deps_type=SourcingDeps,
    output_type=SourcingAnalysis,
    tools=[duckduckgo_search_tool()],
    instructions=(
        "You are a commodity sourcing analyst. Identify the primary sourcing regions, "
        "concentration risk level, and recent news for the requested commodity. "
        "Use the commodity profile tool first, then search for recent news. "
        "Be specific about countries, production shares, and current events."
    ),
)


@sourcing_agent.tool_plain
def get_commodity_profile(commodity: str) -> str:
    """Look up pre-built commodity profile with sourcing regions and risk context."""
    profile = lookup_commodity_profile(commodity)
    if profile is None:
        return f"No pre-built profile for '{commodity}'. Use web search to find sourcing information."
    return str(profile)
