"""Write a readable Markdown report and JSON snapshot from dashboard summaries."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api"))

from app.services.quality_dashboard import build_quality_dashboard  # noqa: E402

REPORT_DIR = PROJECT_ROOT / "docs" / "reports"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "test-results"


def create_report() -> tuple[Path, Path]:
    dashboard = build_quality_dashboard()
    now = datetime.now(UTC)
    snapshot = dashboard.model_dump(mode="json")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "quality-dashboard-latest.json"
    markdown_path = REPORT_DIR / "quality-report-latest.md"
    json_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# ShopGuard Quality Report",
        "",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Overall status: **{dashboard.overall_status.replace('_', ' ')}**",
        f"Passing suites: **{dashboard.passing_suites} of {dashboard.total_suites}**",
        "",
        "| Check | Status | Summary | Last run |",
        "|---|---|---|---|",
    ]
    for run in dashboard.latest_runs:
        last_run = run.run_at.strftime("%Y-%m-%d %H:%M UTC") if run.run_at else "Not run yet"
        summary = run.summary.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {run.suite_name} | {run.status} | {summary} | {last_run} |")
    lines += [
        "",
        "This report summarizes saved test results. A check marked `not_run` has no saved result.",
        "",
        "Detailed artifacts and machine-readable results are stored in `outputs/test-results/`.",
        "",
    ]
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return markdown_path, json_path


if __name__ == "__main__":
    report, snapshot = create_report()
    print(f"Wrote {report.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {snapshot.relative_to(PROJECT_ROOT)}")
