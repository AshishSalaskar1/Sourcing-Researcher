from pydantic import BaseModel, Field


class SourceRegion(BaseModel):
    """A sourcing region for a commodity."""

    country: str
    region: str | None = None
    share_percent: float | None = Field(
        None, description="Approximate share of global production"
    )
    notes: str | None = None


class SourcingAnalysis(BaseModel):
    """Output from the SourcingAgent."""

    commodity: str
    primary_regions: list[SourceRegion]
    concentration_risk: str = Field(description="Low/Medium/High/Critical")
    recent_news: list[str] = Field(
        default_factory=list, description="Recent news headlines"
    )
    summary: str = Field(description="Brief sourcing summary")


class RiskFactor(BaseModel):
    """Individual risk factor with score and explanation."""

    domain: str = Field(
        description="Risk domain: climate, geopolitical, market, logistics, regulatory, biological, supplier, esg"
    )
    score: float = Field(ge=0, le=10, description="Risk score 0-10")
    explanation: str
    signals: list[str] = Field(
        default_factory=list, description="Supporting evidence"
    )


class RiskAssessment(BaseModel):
    """Output from the DataAgent."""

    commodity: str
    risk_factors: list[RiskFactor]
    composite_score: float = Field(
        ge=0, le=10, description="Weighted composite risk score"
    )
    risk_level: str = Field(description="Low/Medium/High/Critical")
    cascade_risks: list[str] = Field(
        default_factory=list, description="Potential cascade scenarios"
    )
    summary: str


class ResilienceOption(BaseModel):
    """A recommended resilience strategy."""

    strategy: str
    description: str
    addresses_risks: list[str] = Field(
        description="Which risk domains this addresses"
    )
    cost_impact: str = Field(description="Low/Medium/High/Very High")
    timeline: str = Field(description="Implementation timeline")
    priority: int = Field(ge=1, le=5, description="1=highest priority")


class RiskReport(BaseModel):
    """Final structured output from the Orchestrator."""

    commodity: str
    overall_risk_score: float = Field(ge=0, le=10)
    risk_level: str = Field(description="Low/Medium/High/Critical")
    sourcing: SourcingAnalysis
    risk_assessment: RiskAssessment
    resilience_options: list[ResilienceOption]
    key_insight: str = Field(description="One-sentence key takeaway")
    sources_used: list[str] = Field(default_factory=list)
