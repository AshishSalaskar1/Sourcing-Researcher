from dataclasses import dataclass
import logging
import time

import httpx
from pydantic_ai import Agent, RunContext

from agents.models import RiskAssessment
from tools.news_search import search_public_news
from tools.weather import fetch_weather_forecast
from tools.world_bank import fetch_world_bank_indicator

logger = logging.getLogger("supply_risk_radar.data_agent")


@dataclass
class DataDeps:
    http_client: httpx.AsyncClient


data_agent = Agent(
    deps_type=DataDeps,
    output_type=RiskAssessment,
    instructions=(
        "You are a supply chain risk data analyst. Gather economic, weather, and disruption "
        "data for the given commodity's sourcing regions. Score each risk domain 0-10 based "
        "on the evidence you find. Identify cascade risks where multiple factors combine. "
        "Use the provided tools to fetch real data, then synthesize into a risk assessment."
    ),
)


@data_agent.tool
async def fetch_weather(ctx: RunContext[DataDeps], latitude: float, longitude: float) -> str:
    """Get 7-day weather forecast for a sourcing region. No API key needed."""
    logger.info("Fetching weather for lat=%s lon=%s", latitude, longitude)
    start_time = time.perf_counter()
    try:
        data = await fetch_weather_forecast(ctx.deps.http_client, latitude, longitude)
    except Exception as exc:
        logger.exception("Weather fetch failed for lat=%s lon=%s", latitude, longitude)
        raise RuntimeError(
            f"fetch_weather failed for coordinates ({latitude}, {longitude})"
        ) from exc
    logger.info(
        "Fetched weather for lat=%s lon=%s in %.2fs",
        latitude,
        longitude,
        time.perf_counter() - start_time,
    )
    return str(data)


@data_agent.tool
async def fetch_economic_indicator(
    ctx: RunContext[DataDeps], country_code: str, indicator: str
) -> str:
    """Fetch economic indicator from World Bank. No API key needed.

    Common indicators: NY.GDP.MKTP.CD (GDP), FP.CPI.TOTL.ZG (inflation),
    NE.TRD.GNFS.ZS (trade % GDP), AG.LND.ARBL.ZS (arable land %).
    """
    logger.info(
        "Fetching economic indicator %s for country %s",
        indicator,
        country_code,
    )
    start_time = time.perf_counter()
    try:
        data = await fetch_world_bank_indicator(
            ctx.deps.http_client, country_code, indicator
        )
    except Exception as exc:
        logger.exception(
            "Economic indicator fetch failed for country=%s indicator=%s",
            country_code,
            indicator,
        )
        raise RuntimeError(
            f"fetch_economic_indicator failed for country '{country_code}' and indicator '{indicator}'"
        ) from exc
    logger.info(
        "Fetched economic indicator %s for country %s in %.2fs",
        indicator,
        country_code,
        time.perf_counter() - start_time,
    )
    return str(data)


@data_agent.tool
async def fetch_disaster_reports(ctx: RunContext[DataDeps], query: str) -> str:
    """Search recent public news for disruption signals. No signup needed."""
    logger.info("Searching public news for query=%r", query)
    start_time = time.perf_counter()
    try:
        data = await search_public_news(query)
    except Exception as exc:
        logger.exception("Public news search failed for query=%r", query)
        raise RuntimeError(f"fetch_disaster_reports failed for query '{query}'") from exc
    logger.info(
        "Completed public news search for query=%r in %.2fs",
        query,
        time.perf_counter() - start_time,
    )
    return str(data)
