"""Checks for converting saved test summaries into dashboard cards."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

API_DIR = Path(__file__).resolve().parents[3] / "apps" / "api"
sys.path.insert(0, str(API_DIR))

from automation.reporting.normalize_junit import build_summary, write_summary  # noqa: E402

from app.main import app  # noqa: E402
from app.services import quality_dashboard  # noqa: E402


def write_json(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report), encoding="utf-8")


def ai_report(run_at: str, passed_count: int = 6) -> dict:
    return {
        "run_at": run_at,
        "case_count": 6,
        "passed_count": passed_count,
        "answer_pass_rate": passed_count / 6,
        "mean_retrieval_precision": 1.0,
        "mean_retrieval_recall": 1.0,
        "latency_ms_p95": 0.1,
    }


def performance_report(run_at: str, passed: bool = True) -> dict:
    return {
        "run_at": run_at,
        "passed": passed,
        "virtual_users": 5,
        "requests": 450,
        "failed_request_rate": 0,
        "successful_check_rate": 1,
        "response_time_ms": {"p95": 12.22},
    }


def test_dashboard_reads_latest_runs_and_calculates_summary(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(quality_dashboard, "OUTPUT_DIR", tmp_path)
    write_json(tmp_path / "ai-evaluation-latest.json", ai_report("2026-11-19T10:00:00+00:00"))
    write_json(
        tmp_path / "performance-latest.json",
        performance_report("2026-11-19T11:00:00+00:00"),
    )

    dashboard = quality_dashboard.build_quality_dashboard()

    assert dashboard.overall_status == "partial"
    assert dashboard.total_suites == 7
    assert dashboard.passing_suites == 2
    assert dashboard.saved_run_count == 2
    performance = next(run for run in dashboard.latest_runs if run.suite_id == "performance")
    assert performance.metrics[-1].value == "12.22 ms"
    assert dashboard.recent_runs[0].suite_id == "performance"


def test_dashboard_shows_not_run_when_no_results_exist(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(quality_dashboard, "OUTPUT_DIR", tmp_path)

    dashboard = quality_dashboard.build_quality_dashboard()

    assert dashboard.overall_status == "not_run"
    assert dashboard.passing_suites == 0
    assert dashboard.saved_run_count == 0
    assert all(run.status == "not_run" for run in dashboard.latest_runs)


def test_dashboard_uses_archived_runs_for_history(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(quality_dashboard, "OUTPUT_DIR", tmp_path)
    write_json(
        tmp_path / "ai-evaluation-older.json",
        ai_report("2026-11-19T10:00:00+00:00", passed_count=5),
    )
    write_json(
        tmp_path / "ai-evaluation-newer.json",
        ai_report("2026-11-19T11:00:00+00:00"),
    )

    dashboard = quality_dashboard.build_quality_dashboard()

    ai_run = next(run for run in dashboard.latest_runs if run.suite_id == "ai-evaluation")
    assert ai_run.status == "passed"
    assert dashboard.saved_run_count == 2
    assert [run.status for run in dashboard.recent_runs] == ["passed", "failed"]


def test_read_only_summary_route_returns_report_cards(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(quality_dashboard, "OUTPUT_DIR", tmp_path)
    write_json(tmp_path / "ai-evaluation-latest.json", ai_report("2026-11-19T10:00:00+00:00"))

    response = TestClient(app).get("/quality/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "partial"
    ai_run = next(run for run in payload["latest_runs"] if run["suite_id"] == "ai-evaluation")
    browser_run = next(run for run in payload["latest_runs"] if run["suite_id"] == "browser")
    assert ai_run["suite_name"] == "AI answer checks"
    assert browser_run["status"] == "not_run"


def test_dashboard_reads_junit_summaries_for_integrated_suites(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(quality_dashboard, "OUTPUT_DIR", tmp_path)
    junit = tmp_path / "api-junit.xml"
    junit.write_text(
        '<testsuite tests="3"><testcase name="one"/><testcase name="two">'
        '<failure message="bad"/></testcase><testcase name="three"><skipped/></testcase>'
        "</testsuite>",
        encoding="utf-8",
    )
    write_summary("api", junit, output_dir=tmp_path)

    dashboard = quality_dashboard.build_quality_dashboard()
    api_run = next(run for run in dashboard.latest_runs if run.suite_id == "api")

    assert api_run.status == "failed"
    assert api_run.metrics[0].value == "3"
    assert api_run.metrics[1].value == "1"
    assert api_run.metrics[2].value == "1"
    assert api_run.metrics[3].value == "1"
    assert api_run.report_file is not None
    assert api_run.report_file.endswith("-junit.xml")


def test_missing_junit_report_is_recorded_as_not_run(tmp_path) -> None:
    summary = build_summary("browser", tmp_path / "missing.xml")

    assert summary["status"] == "not_run"
    assert summary["test_count"] == 0


def test_unreadable_junit_report_is_failed(tmp_path) -> None:
    report = tmp_path / "broken.xml"
    report.write_text("not XML", encoding="utf-8")

    summary = build_summary("browser", report)

    assert summary["status"] == "failed"
    assert "could not be read" in str(summary["summary"])
