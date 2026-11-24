import { useEffect, useState } from "react";

type Status = "passed" | "failed" | "not_run";
type Metric = { label: string; value: string };
type Run = {
  run_id: string;
  suite_id: "project-tests" | "browser" | "api" | "api-components" | "ai-security" | "ai-evaluation" | "performance";
  suite_name: string;
  status: Status;
  summary: string;
  run_at: string | null;
  report_file: string | null;
  metrics: Metric[];
};
type DashboardData = {
  overall_status: "passed" | "failed" | "partial" | "not_run";
  total_suites: number;
  passing_suites: number;
  saved_run_count: number;
  last_updated: string | null;
  latest_runs: Run[];
  recent_runs: Run[];
};

function formatDate(value: string | null): string {
  if (!value) return "Not run yet";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function statusLabel(status: string): string {
  return status.replaceAll("_", " ");
}

function suiteLabel(suiteId: Run["suite_id"]): string {
  const labels: Record<Run["suite_id"], string> = {
    "project-tests": "Project tests",
    browser: "Browser",
    api: "API",
    "api-components": "API component",
    "ai-security": "AI safety",
    "ai-evaluation": "AI answers",
    performance: "Performance",
  };
  return labels[suiteId];
}

export function QualityDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/quality/summary");
      if (!response.ok) throw new Error(`Dashboard request failed (${response.status})`);
      setData((await response.json()) as DashboardData);
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <main className="quality-page page-shell">
      <header className="quality-topbar">
        <a className="brand" href="#catalog" aria-label="Return to ShopGuard Market">
          <span className="brand-mark">S</span> ShopGuard <span>Quality</span>
        </a>
        <nav aria-label="Quality dashboard navigation">
          <a href="#catalog">Back to shop</a>
        </nav>
      </header>

      <section className="quality-hero">
        <div>
          <p className="eyebrow">The shop's health at a glance</p>
          <h1>Quality <em>dashboard.</em></h1>
          <p>See saved browser, API, AI, and speed checks in one place.</p>
        </div>
        <button className="button button-dark" onClick={() => void refresh()} disabled={loading}>
          {loading ? "Loading..." : "Refresh results"}
          <span aria-hidden="true">↻</span>
        </button>
      </section>

      {error && <p className="quality-error" role="alert">{error}</p>}
      {loading && !data && <p className="quality-message" role="status">Getting the saved test results...</p>}
      {!loading && !error && data && (
        <>
          <section className="quality-kpis" aria-label="Quality summary">
            <article className="quality-kpi">
              <span>Overall status</span>
              <strong className={`quality-status status-${data.overall_status}`}>
                {statusLabel(data.overall_status)}
              </strong>
            </article>
            <article className="quality-kpi">
              <span>Checks passing</span>
              <strong>{data.passing_suites} / {data.total_suites}</strong>
            </article>
            <article className="quality-kpi">
              <span>Saved runs</span>
              <strong>{data.saved_run_count}</strong>
            </article>
            <article className="quality-kpi">
              <span>Most recent result</span>
              <strong className="quality-date">{formatDate(data.last_updated)}</strong>
            </article>
          </section>

          <section className="quality-section" aria-labelledby="latest-heading">
            <div className="quality-section-heading">
              <div><p className="eyebrow">Current picture</p><h2 id="latest-heading">Latest checks</h2></div>
              <p>Run a test command to update these cards.</p>
            </div>
            <div className="quality-run-grid">
              {data.latest_runs.map((run) => (
                <article className="quality-run-card" key={run.suite_id}>
                  <div className="quality-run-top">
                    <div><p className="eyebrow">{suiteLabel(run.suite_id)}</p><h3>{run.suite_name}</h3></div>
                    <span className={`quality-status status-${run.status}`}>{statusLabel(run.status)}</span>
                  </div>
                  <p className="quality-run-summary">{run.summary}</p>
                  <p className="quality-run-date">Last run: {formatDate(run.run_at)}</p>
                  {run.metrics.length > 0 && (
                    <dl className="quality-metrics">
                      {run.metrics.map((metric) => (
                        <div key={metric.label}><dt>{metric.label}</dt><dd>{metric.value}</dd></div>
                      ))}
                    </dl>
                  )}
                  {run.report_file && <p className="quality-report-path">Report: <code>{run.report_file}</code></p>}
                </article>
              ))}
            </div>
          </section>

          <section className="quality-section quality-history" aria-labelledby="history-heading">
            <div className="quality-section-heading">
              <div><p className="eyebrow">Saved result files</p><h2 id="history-heading">Recent run history</h2></div>
            </div>
            {data.recent_runs.length === 0 ? (
              <p className="quality-message">No saved runs yet. Run one of the project test commands to add results.</p>
            ) : (
              <div className="quality-history-list">
                {data.recent_runs.map((run) => (
                  <article className="quality-history-row" key={run.run_id}>
                    <span className={`quality-status status-${run.status}`}>{statusLabel(run.status)}</span>
                    <strong>{run.suite_name}</strong>
                    <span>{run.summary}</span>
                    <time>{formatDate(run.run_at)}</time>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
      <footer className="quality-footer"><span>ShopGuard Quality</span><span>Test summaries only. No customer details are shown.</span></footer>
    </main>
  );
}
