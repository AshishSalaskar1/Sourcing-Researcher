export interface SourceRegion {
  country: string;
  region?: string | null;
  share_percent?: number | null;
  notes?: string | null;
}

export interface SourcingAnalysis {
  commodity: string;
  primary_regions: SourceRegion[];
  concentration_risk: string;
  recent_news: string[];
  summary: string;
}

export interface RiskFactor {
  domain: string;
  score: number;
  explanation: string;
  signals: string[];
}

export interface RiskAssessment {
  commodity: string;
  risk_factors: RiskFactor[];
  composite_score: number;
  risk_level: string;
  cascade_risks: string[];
  summary: string;
}

export interface ResilienceOption {
  strategy: string;
  description: string;
  addresses_risks: string[];
  cost_impact: string;
  timeline: string;
  priority: number;
}

export interface RiskReport {
  commodity: string;
  overall_risk_score: number;
  risk_level: string;
  sourcing: SourcingAnalysis;
  risk_assessment: RiskAssessment;
  resilience_options: ResilienceOption[];
  key_insight: string;
  sources_used: string[];
}

export interface AnalyzeResponse {
  report: RiskReport;
  tool_calls: string[];
  duration_seconds: number;
  debug: DebugTrace;
}

export interface DebugToolCall {
  id: string;
  label: string;
  args_summary?: string | null;
  args_detail?: string | null;
  output_summary?: string | null;
  output_detail?: string | null;
}

export interface DebugNode {
  id: string;
  label: string;
  kind: "agent" | "tool";
  depth: number;
  order: number;
  parent_id?: string | null;
  input_summary?: string | null;
  input_detail?: string | null;
  output_summary?: string | null;
  output_detail?: string | null;
  output_data?: unknown;
  duration_seconds?: number | null;
  tool_calls: DebugToolCall[];
}

export interface DebugEdge {
  source: string;
  target: string;
  label?: string | null;
}

export interface DebugTrace {
  root_node_id: string;
  nodes: DebugNode[];
  edges: DebugEdge[];
}
