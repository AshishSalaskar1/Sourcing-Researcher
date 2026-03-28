import { LoaderCircle, Radar, Sparkles } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import { ReportView } from "./components/report-view";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./components/ui/card";
import { Textarea } from "./components/ui/textarea";
import type { AnalyzeResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const starterPrompts = [
  "Analyze cocoa supply chain risks",
  "What are the supply risks for vanilla?",
  "Assess sunflower oil disruption exposure",
];

export default function App() {
  const [prompt, setPrompt] = useState(starterPrompts[0]);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = useMemo(() => prompt.trim().length > 0 && !isLoading, [prompt, isLoading]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });

      const payload = (await response.json()) as AnalyzeResponse | { detail?: string };

      if (!response.ok) {
        throw new Error("detail" in payload && payload.detail ? payload.detail : "Analysis failed.");
      }

      setResult(payload as AnalyzeResponse);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to reach the backend.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="app-header card aurora-panel">
        <div className="app-header-main">
          <div className="section-heading">
            <Sparkles size={18} />
            <span className="app-header-kicker">Supply Risk Radar</span>
          </div>
          <p className="app-header-copy">
            Multi-agent sourcing, risk, and resilience analysis with a cleaner API boundary and an
            internal debug graph for execution traces.
          </p>
        </div>
        <div className="app-header-meta">
          <Badge className="hero-badge">FastAPI + React</Badge>
          <span className="muted-copy">API base: {API_BASE_URL}</span>
        </div>
      </section>

      <div className="workspace-stack">
        <Card className="composer-card composer-panel">
          <CardHeader>
            <div className="section-heading">
              <Sparkles size={18} />
              <CardTitle>Start an analysis</CardTitle>
            </div>
            <CardDescription>
              Ask about a commodity, ingredient, or disruption scenario.
            </CardDescription>
          </CardHeader>
          <CardContent className="stack">
            <div className="prompt-list">
              {starterPrompts.map((item) => (
                <button
                  key={item}
                  type="button"
                  className="prompt-chip accent-chip"
                  onClick={() => setPrompt(item)}
                >
                  {item}
                </button>
              ))}
            </div>

            <form className="stack" onSubmit={handleSubmit}>
              <Textarea
                rows={6}
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="Ask about supply risks for any ingredient or commodity..."
              />
              <div className="composer-actions">
                <Button disabled={!canSubmit} type="submit">
                  {isLoading ? (
                    <>
                      <LoaderCircle className="spin" size={16} />
                      Analyzing...
                    </>
                  ) : (
                    "Run analysis"
                  )}
                </Button>
              </div>
            </form>

            {error && <div className="error-banner">{error}</div>}
          </CardContent>
        </Card>

        <section className="results-panel">
          {result ? (
            <ReportView data={result} />
          ) : (
            <Card className="empty-state">
              <CardContent className="empty-state-content">
                <Radar size={28} />
                <h2>No report yet</h2>
                <p>
                  Submit a prompt to view sourcing concentration, risk factors, and resilience
                  recommendations from the backend API.
                </p>
              </CardContent>
            </Card>
          )}
        </section>
      </div>
    </main>
  );
}
