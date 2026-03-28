from dataclasses import dataclass
import logging
import time

import httpx
from pydantic_ai import Agent, RunContext, UsageLimits

from agents.data_agent import DataDeps, data_agent
from agents.models import RiskReport
from agents.resilience import resilience_agent
from agents.sourcing import SourcingDeps, sourcing_agent

# Per-query token budget to prevent runaway costs (DR-04)
USAGE_LIMITS = UsageLimits(request_limit=20, total_tokens_limit=50_000)
logger = logging.getLogger("supply_risk_radar.orchestrator")


@dataclass
class OrchestratorDeps:
    http_client: httpx.AsyncClient


orchestrator = Agent(
    deps_type=OrchestratorDeps,
    output_type=RiskReport,
    instructions=(
        "You are the Supply Risk Radar orchestrator. When a user asks about supply risks "
        "for a commodity or ingredient, coordinate a comprehensive analysis:\n"
        "1. Call analyze_sourcing to identify where it comes from and recent news\n"
        "2. Call analyze_risks with the sourcing regions to gather data-driven risk signals\n"
        "3. Call analyze_resilience with the identified risks to get recommendations\n"
        "4. Synthesize everything into a complete RiskReport\n\n"
        "Always call the tools in order: sourcing first, then risks, then resilience. "
        "Each tool returns structured analysis from a specialist agent."
    ),
)


@orchestrator.tool
async def analyze_sourcing(ctx: RunContext[OrchestratorDeps], commodity: str) -> str:
    """Identify sourcing regions, concentration risk, and recent news for a commodity.
    Call this first to understand where the commodity comes from."""
    logger.info("Starting sourcing analysis for %s", commodity)
    start_time = time.perf_counter()
    try:
        result = await sourcing_agent.run(
            f"Analyze sourcing for: {commodity}",
            deps=SourcingDeps(http_client=ctx.deps.http_client),
            model=ctx.model,
            usage=ctx.usage,
        )
    except Exception as exc:
        logger.exception("Sourcing analysis failed for %s", commodity)
        raise RuntimeError(f"analyze_sourcing failed for commodity '{commodity}'") from exc
    logger.info(
        "Completed sourcing analysis for %s in %.2fs",
        commodity,
        time.perf_counter() - start_time,
    )
    return result.output.model_dump_json()


@orchestrator.tool
async def analyze_risks(
    ctx: RunContext[OrchestratorDeps], commodity: str, sourcing_summary: str
) -> str:
    """Gather economic, weather, and disaster data to assess risks for sourcing regions.
    Call this after analyze_sourcing, passing the sourcing summary."""
    logger.info("Starting risk analysis for %s", commodity)
    start_time = time.perf_counter()
    try:
        result = await data_agent.run(
            f"Assess supply chain risks for {commodity}. Sourcing context: {sourcing_summary}",
            deps=DataDeps(http_client=ctx.deps.http_client),
            model=ctx.model,
            usage=ctx.usage,
        )
    except Exception as exc:
        logger.exception("Risk analysis failed for %s", commodity)
        raise RuntimeError(f"analyze_risks failed for commodity '{commodity}'") from exc
    logger.info(
        "Completed risk analysis for %s in %.2fs",
        commodity,
        time.perf_counter() - start_time,
    )
    return result.output.model_dump_json()


@orchestrator.tool
async def analyze_resilience(
    ctx: RunContext[OrchestratorDeps], commodity: str, risk_summary: str
) -> str:
    """Recommend resilience strategies matched to identified risks.
    Call this after analyze_risks, passing the risk summary."""
    logger.info("Starting resilience analysis for %s", commodity)
    start_time = time.perf_counter()
    try:
        result = await resilience_agent.run(
            f"Recommend resilience strategies for {commodity}. Risk context: {risk_summary}",
            model=ctx.model,
            usage=ctx.usage,
        )
    except Exception as exc:
        logger.exception("Resilience analysis failed for %s", commodity)
        raise RuntimeError(f"analyze_resilience failed for commodity '{commodity}'") from exc
    logger.info(
        "Completed resilience analysis for %s in %.2fs",
        commodity,
        time.perf_counter() - start_time,
    )
    return str([opt.model_dump() for opt in result.output])
