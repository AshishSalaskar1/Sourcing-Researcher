from dataclasses import dataclass
import logging
import time

import httpx
from pydantic_ai import Agent, RunContext, UsageLimits

from backend.app.debug_trace import DebugTraceBuilder, collect_tool_calls
from backend.agents.data_agent import DataDeps, data_agent
from backend.agents.models import (
    ResilienceOption,
    RiskAssessment,
    RiskFactor,
    RiskReport,
    SourcingAnalysis,
    SourceRegion,
)
from backend.agents.resilience import resilience_agent
from backend.agents.sourcing import SourcingDeps, sourcing_agent

# Per-query token budget to prevent runaway costs (DR-04)
USAGE_LIMITS = UsageLimits(request_limit=20, total_tokens_limit=50_000)
logger = logging.getLogger("supply_risk_radar.orchestrator")


def _fallback_sourcing_analysis(commodity: str, error: Exception) -> SourcingAnalysis:
    return SourcingAnalysis(
        commodity=commodity,
        primary_regions=[
            SourceRegion(
                country="Unknown",
                notes=(
                    "Sourcing data could not be resolved from available sources for this prompt."
                ),
            )
        ],
        concentration_risk="Medium",
        recent_news=[],
        summary=(
            f"Detailed sourcing data for {commodity} was unavailable, so this report uses "
            "limited fallback context."
        ),
    )


def _fallback_risk_assessment(commodity: str, error: Exception) -> RiskAssessment:
    error_text = f"{type(error).__name__}: {error}"
    return RiskAssessment(
        commodity=commodity,
        risk_factors=[
            RiskFactor(
                domain="market",
                score=5.0,
                explanation=(
                    "Primary risk signals are incomplete because one or more external data "
                    "sources were unavailable."
                ),
                signals=[
                    "Fallback assessment used due to missing upstream data.",
                    error_text,
                ],
            )
        ],
        composite_score=5.0,
        risk_level="Medium",
        cascade_risks=[
            "Incomplete upstream data may hide secondary climate, logistics, or pricing signals."
        ],
        summary=(
            f"Risk analysis for {commodity} used fallback logic because at least one required "
            "data source could not be retrieved."
        ),
    )


def _fallback_resilience_options(commodity: str, error: Exception) -> list[ResilienceOption]:
    error_text = f"{type(error).__name__}: {error}"
    return [
        ResilienceOption(
            strategy="Diversify sourcing footprint",
            description=(
                f"Use broader sourcing coverage for {commodity} while detailed resilience "
                "modeling is unavailable."
            ),
            addresses_risks=["market", "supplier", "logistics"],
            cost_impact="Medium",
            timeline="1-2 quarters",
            priority=1,
        ),
        ResilienceOption(
            strategy="Increase monitoring and contingency triggers",
            description=(
                "Track price, weather, and disruption signals more closely until richer data "
                f"returns. Fallback reason: {error_text}"
            ),
            addresses_risks=["market", "climate", "logistics"],
            cost_impact="Low",
            timeline="Immediate",
            priority=2,
        ),
    ]


@dataclass
class OrchestratorDeps:
    http_client: httpx.AsyncClient
    debug_trace: DebugTraceBuilder | None = None


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
        output = result.output
        tool_calls = collect_tool_calls(result)
    except Exception as exc:
        logger.exception("Sourcing analysis failed for %s", commodity)
        output = _fallback_sourcing_analysis(commodity, exc)
        tool_calls = []
    logger.info(
        "Completed sourcing analysis for %s in %.2fs",
        commodity,
        time.perf_counter() - start_time,
    )
    if ctx.deps.debug_trace is not None:
        ctx.deps.debug_trace.record_agent_run(
            node_id="sourcing-agent",
            label="Sourcing Agent",
            edge_label="analyze_sourcing",
            input_summary=f"Analyze sourcing for: {commodity}",
            output_data=output,
            duration_seconds=time.perf_counter() - start_time,
            tool_calls=tool_calls,
        )
    return output.model_dump_json()


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
        output = result.output
        tool_calls = collect_tool_calls(result)
    except Exception as exc:
        logger.exception("Risk analysis failed for %s", commodity)
        output = _fallback_risk_assessment(commodity, exc)
        tool_calls = []
    logger.info(
        "Completed risk analysis for %s in %.2fs",
        commodity,
        time.perf_counter() - start_time,
    )
    if ctx.deps.debug_trace is not None:
        ctx.deps.debug_trace.record_agent_run(
            node_id="risk-agent",
            label="Risk Agent",
            edge_label="analyze_risks",
            input_summary=(
                f"Assess supply chain risks for {commodity}. "
                f"Sourcing context: {sourcing_summary}"
            ),
            output_data=output,
            duration_seconds=time.perf_counter() - start_time,
            tool_calls=tool_calls,
        )
    return output.model_dump_json()


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
        output = result.output
        tool_calls = collect_tool_calls(result)
    except Exception as exc:
        logger.exception("Resilience analysis failed for %s", commodity)
        output = _fallback_resilience_options(commodity, exc)
        tool_calls = []
    logger.info(
        "Completed resilience analysis for %s in %.2fs",
        commodity,
        time.perf_counter() - start_time,
    )
    if ctx.deps.debug_trace is not None:
        ctx.deps.debug_trace.record_agent_run(
            node_id="resilience-agent",
            label="Resilience Agent",
            edge_label="analyze_resilience",
            input_summary=(
                f"Recommend resilience strategies for {commodity}. "
                f"Risk context: {risk_summary}"
            ),
            output_data=output,
            duration_seconds=time.perf_counter() - start_time,
            tool_calls=tool_calls,
        )
    return str([opt.model_dump() for opt in output])
