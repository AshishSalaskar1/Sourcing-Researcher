from dataclasses import dataclass
import logging
import os
import time

import httpx
from dotenv import load_dotenv

from backend.app.debug_trace import DebugTrace, DebugTraceBuilder
from backend.agents import USAGE_LIMITS, OrchestratorDeps, orchestrator
from backend.agents.models import RiskReport

load_dotenv()

logger = logging.getLogger("supply_risk_radar.analysis_service")


@dataclass
class AnalysisResult:
    report: RiskReport
    tool_calls: list[str]
    duration_seconds: float
    debug: DebugTrace


def _collect_tool_calls(agent_result) -> list[str]:
    tool_calls: list[str] = []
    for message in agent_result.all_messages():
        for part in message.parts:
            tool_name = getattr(part, "tool_name", None)
            if tool_name and tool_name not in tool_calls:
                tool_calls.append(tool_name)
    return tool_calls


async def run_supply_risk_analysis(prompt: str) -> AnalysisResult:
    model_name = os.environ.get("AZURE_OPENAI_MODEL", "gpt-4o")
    logger.info("Starting analysis with model azure:%s", model_name)
    start_time = time.perf_counter()
    debug_trace = DebugTraceBuilder(prompt=prompt)

    async with httpx.AsyncClient(timeout=60) as client:
        agent_result = await orchestrator.run(
            prompt,
            model=f"azure:{model_name}",
            deps=OrchestratorDeps(http_client=client, debug_trace=debug_trace),
            usage_limits=USAGE_LIMITS,
        )

    duration_seconds = time.perf_counter() - start_time
    debug_trace.set_root_output(agent_result.output)
    logger.info("Analysis completed in %.2fs", duration_seconds)
    return AnalysisResult(
        report=agent_result.output,
        tool_calls=_collect_tool_calls(agent_result),
        duration_seconds=duration_seconds,
        debug=debug_trace.build(),
    )
