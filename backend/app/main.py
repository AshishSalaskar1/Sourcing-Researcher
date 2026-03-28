import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse
from backend.app.services.analysis import run_supply_risk_analysis
from backend.app.settings import get_cors_origins

load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("supply_risk_radar.api")

app = FastAPI(
    title="Supply Risk Radar API",
    version="0.1.0",
    description="FastAPI backend for the Supply Risk Radar multi-agent workflow.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        result = await run_supply_risk_analysis(payload.prompt.strip())
    except Exception as exc:
        logger.exception("API analysis failed")
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}") from exc

    return AnalyzeResponse(
        report=result.report,
        tool_calls=result.tool_calls,
        duration_seconds=round(result.duration_seconds, 2),
        debug=result.debug,
    )
