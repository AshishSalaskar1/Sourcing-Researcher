from pydantic import BaseModel, Field

from backend.app.debug_trace import DebugTrace
from backend.agents.models import RiskReport


class AnalyzeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2_000)


class AnalyzeResponse(BaseModel):
    report: RiskReport
    tool_calls: list[str] = Field(default_factory=list)
    duration_seconds: float
    debug: DebugTrace


class HealthResponse(BaseModel):
    status: str
