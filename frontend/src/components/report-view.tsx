import { AlertTriangle, ArrowRight, Bug, Globe2, ShieldCheck, Sparkles } from "lucide-react";
import { useState } from "react";

import { DebugTracePanel } from "./debug-trace-panel";
import { formatScore } from "../lib/utils";
import type { AnalyzeResponse } from "../types";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";

type ReportViewProps = {
  data: AnalyzeResponse;
};

function MetricCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "default" | "warning" | "cool" | "success";
}) {
  const toneClass =
    tone === "warning"
      ? "metric-card metric-card-warning"
      : tone === "cool"
        ? "metric-card metric-card-cool"
        : tone === "success"
          ? "metric-card metric-card-success"
          : "metric-card";

  return (
    <Card className={toneClass}>
      <CardContent>
        <p className="metric-label">{label}</p>
        <p className="metric-value">{value}</p>
      </CardContent>
    </Card>
  );
}

export function ReportView({ data }: ReportViewProps) {
  const { report, tool_calls, duration_seconds, debug } = data;
  const [isDebugOpen, setIsDebugOpen] = useState(false);

  return (
    <>
      <div className="report-shell">
        <div className="metrics-grid">
          <MetricCard label="Overall risk" value={formatScore(report.overall_risk_score)} tone="warning" />
          <MetricCard label="Risk level" value={report.risk_level} tone="cool" />
          <MetricCard label="Concentration" value={report.sourcing.concentration_risk} tone="success" />
          <MetricCard label="API turnaround" value={`${duration_seconds.toFixed(2)}s`} tone="cool" />
        </div>

        <Card className="hero-card insight-card">
          <CardHeader>
            <div className="report-hero-heading">
              <div className="stack debug-heading-copy">
                <div className="section-heading">
                  <Sparkles size={18} />
                  <CardTitle>{report.commodity}</CardTitle>
                </div>
                <CardDescription>{report.key_insight}</CardDescription>
              </div>
              <Button
                variant="ghost"
                type="button"
                className="debug-trigger"
                onClick={() => setIsDebugOpen(true)}
                aria-label="Open debug graph"
                title="Open debug graph"
              >
                <Bug size={16} />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="tool-call-list">
            {tool_calls.map((toolName) => (
              <Badge key={toolName}>{toolName}</Badge>
            ))}
          </CardContent>
        </Card>

        <div className="content-grid">
          <Card className="sourcing-card">
            <CardHeader>
              <div className="section-heading">
                <Globe2 size={18} />
                <CardTitle>Sourcing analysis</CardTitle>
              </div>
              <CardDescription>{report.sourcing.summary}</CardDescription>
            </CardHeader>
            <CardContent className="stack">
              {report.sourcing.primary_regions.map((region) => (
                <div className="detail-row" key={`${region.country}-${region.region ?? "main"}`}>
                  <div>
                    <p className="detail-title">{region.country}</p>
                    <p className="detail-subtitle">
                      {[region.region, region.share_percent ? `${region.share_percent}% share` : undefined]
                        .filter(Boolean)
                        .join(" • ") || "Primary source region"}
                    </p>
                  </div>
                  <p className="detail-copy">{region.notes || "No additional notes provided."}</p>
                </div>
              ))}

              {report.sourcing.recent_news.length > 0 && (
                <div className="stack">
                  <p className="subsection-title">Recent signals</p>
                  <ul className="bullet-list">
                    {report.sourcing.recent_news.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="risk-card">
            <CardHeader>
              <div className="section-heading">
                <AlertTriangle size={18} />
                <CardTitle>Risk assessment</CardTitle>
              </div>
              <CardDescription>{report.risk_assessment.summary}</CardDescription>
            </CardHeader>
            <CardContent className="stack">
              {report.risk_assessment.risk_factors.map((factor) => (
                <div className="factor-card" key={`${factor.domain}-${factor.score}`}>
                  <div className="factor-header">
                    <div>
                      <p className="detail-title">{factor.domain}</p>
                      <p className="detail-subtitle">{factor.explanation}</p>
                    </div>
                    <Badge>{formatScore(factor.score)}</Badge>
                  </div>
                  {factor.signals.length > 0 && (
                    <ul className="bullet-list subtle">
                      {factor.signals.map((signal) => (
                        <li key={signal}>{signal}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}

              {report.risk_assessment.cascade_risks.length > 0 && (
                <div className="stack">
                  <p className="subsection-title">Cascade risks</p>
                  <ul className="bullet-list">
                    {report.risk_assessment.cascade_risks.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="resilience-card">
          <CardHeader>
            <div className="section-heading">
              <ShieldCheck size={18} />
              <CardTitle>Resilience recommendations</CardTitle>
            </div>
            <CardDescription>
              Actions prioritized by impact, feasibility, and risk coverage.
            </CardDescription>
          </CardHeader>
          <CardContent className="recommendation-grid">
            {report.resilience_options.map((option) => (
              <div className="recommendation-card" key={`${option.strategy}-${option.priority}`}>
                <div className="factor-header">
                  <div>
                    <p className="detail-title">{option.strategy}</p>
                    <p className="detail-subtitle">
                      Priority {option.priority} • {option.timeline}
                    </p>
                  </div>
                  <Badge>{option.cost_impact}</Badge>
                </div>
                <p className="detail-copy">{option.description}</p>
                <div className="tag-list">
                  {option.addresses_risks.map((risk) => (
                    <Badge key={risk}>{risk}</Badge>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {report.sources_used.length > 0 && (
          <Card className="sources-card">
            <CardHeader>
              <CardTitle>Sources used</CardTitle>
              <CardDescription>Data references surfaced during the analysis.</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="bullet-list">
                {report.sources_used.map((source) => (
                  <li key={source} className="source-row">
                    <ArrowRight size={14} />
                    <span>{source}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      {isDebugOpen && <DebugTracePanel trace={debug} onClose={() => setIsDebugOpen(false)} />}
    </>
  );
}
