"""Read saved, safe-to-display quality reports for the local dashboard."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from app.core.config import PROJECT_ROOT
from app.domain.schemas import QualityDashboardRead, QualityRunMetric, QualityRunRead

logger = logging.getLogger(__name__)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "test-results"
RUN_LIMIT = 20
Status = Literal["passed", "failed", "not_run"]
SUITES = {
    "project-tests": ("Project and dashboard tests", "make project-test"),
    "browser": ("Browser journey checks", "make ui-test-chromium"),
    "api": ("API behavior checks", "make api-test"),
    "api-components": ("API component checks", "make api-component-test"),
    "ai-security": ("AI safety checks", "make ai-security-test"),
    "ai-evaluation": ("AI answer checks", "make ai-eval"),
    "performance": ("Shop API speed check", "make perf-smoke"),
}


def _as_number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _read_report(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("Could not read quality report %s", path.name)
        return None
    return data if isinstance(data, dict) else None


def _report_file(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return path.name


def _report_time(data: dict[str, Any], path: Path) -> datetime:
    run_at = data.get("run_at")
    if isinstance(run_at, str):
        try:
            parsed = datetime.fromisoformat(run_at.replace("Z", "+00:00"))
            return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed
        except ValueError:
            logger.warning("Invalid run time in quality report %s", path.name)
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)


def _paths(prefix: str) -> list[Path]:
    latest = OUTPUT_DIR / f"{prefix}-latest.json"
    archived = sorted(
        (path for path in OUTPUT_DIR.glob(f"{prefix}-*.json") if path != latest),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if archived:
        return archived[:RUN_LIMIT]
    return [latest] if latest.exists() else []


def _ai_run(path: Path) -> QualityRunRead | None:
    data = _read_report(path)
    if data is None:
        return None
    cases = int(_as_number(data.get("case_count")))
    passed = int(_as_number(data.get("passed_count")))
    if cases < 1:
        status: Status = "failed"
    else:
        status = "passed" if passed == cases else "failed"
    at = _report_time(data, path)
    return QualityRunRead(
        run_id=path.stem,
        suite_id="ai-evaluation",
        suite_name="AI answer checks",
        status=status,
        summary=f"{passed} of {cases} example questions passed.",
        run_at=at,
        report_file=_report_file(path),
        metrics=[
            QualityRunMetric(
                label="Answer checks",
                value=f"{_as_number(data.get('answer_pass_rate')):.0%}",
            ),
            QualityRunMetric(
                label="Retrieval precision",
                value=f"{_as_number(data.get('mean_retrieval_precision')):.0%}",
            ),
            QualityRunMetric(
                label="Retrieval recall",
                value=f"{_as_number(data.get('mean_retrieval_recall')):.0%}",
            ),
            QualityRunMetric(
                label="P95 time", value=f"{_as_number(data.get('latency_ms_p95')):.2f} ms"
            ),
        ],
    )


def _performance_run(path: Path) -> QualityRunRead | None:
    data = _read_report(path)
    if data is None:
        return None
    p95 = _as_number(data.get("response_time_ms", {}).get("p95"))
    failed_rate = _as_number(data.get("failed_request_rate"))
    request_count = int(_as_number(data.get("requests")))
    status: Status = "passed" if data.get("passed") is True else "failed"
    at = _report_time(data, path)
    return QualityRunRead(
        run_id=path.stem,
        suite_id="performance",
        suite_name="Shop API speed check",
        status=status,
        summary=f"{request_count} requests; {failed_rate:.1%} failed; p95 {p95:.2f} ms.",
        run_at=at,
        report_file=_report_file(path),
        metrics=[
            QualityRunMetric(label="Pretend shoppers", value=str(data.get("virtual_users", "-"))),
            QualityRunMetric(label="Requests", value=str(request_count)),
            QualityRunMetric(label="Failed", value=f"{failed_rate:.1%}"),
            QualityRunMetric(label="P95 time", value=f"{p95:.2f} ms"),
        ],
    )


def _junit_run(path: Path, suite_id: str) -> QualityRunRead | None:
    data = _read_report(path)
    if data is None:
        return None
    suite_name, _ = SUITES[suite_id]
    failed = int(_as_number(data.get("failed_count")))
    errors = int(_as_number(data.get("error_count")))
    tests = int(_as_number(data.get("test_count")))
    saved_status = data.get("status")
    status: Status = saved_status if saved_status in {"passed", "failed", "not_run"} else "failed"
    saved_report = data.get("report_file")
    return QualityRunRead(
        run_id=path.stem,
        suite_id=suite_id,  # type: ignore[arg-type]
        suite_name=suite_name,
        status=status,
        summary=str(data.get("summary", f"{tests} checks; {failed + errors} failed.")),
        run_at=_report_time(data, path),
        report_file=str(saved_report) if saved_report else _report_file(path),
        metrics=[
            QualityRunMetric(label="Checks", value=str(tests)),
            QualityRunMetric(label="Passed", value=str(int(_as_number(data.get("passed_count"))))),
            QualityRunMetric(label="Failed", value=str(failed + errors)),
            QualityRunMetric(
                label="Skipped", value=str(int(_as_number(data.get("skipped_count"))))
            ),
        ],
    )


def _not_run(suite_id: str) -> QualityRunRead:
    name, command = SUITES[suite_id]
    return QualityRunRead(
        run_id=f"{suite_id}-not-run",
        suite_id=suite_id,  # type: ignore[arg-type]
        suite_name=name,
        status="not_run",
        summary=f"No saved result yet. Run {command} to add one.",
        run_at=None,
        report_file=None,
        metrics=[],
    )


def build_quality_dashboard() -> QualityDashboardRead:
    """Build current suite statuses and the most recent saved run history."""
    all_runs: list[QualityRunRead] = []
    report_readers = {
        "project-tests": lambda path: _junit_run(path, "project-tests"),
        "browser": lambda path: _junit_run(path, "browser"),
        "api": lambda path: _junit_run(path, "api"),
        "api-components": lambda path: _junit_run(path, "api-components"),
        "ai-security": lambda path: _junit_run(path, "ai-security"),
        "ai-evaluation": _ai_run,
        "performance": _performance_run,
    }
    for suite_id, reader in report_readers.items():
        for path in _paths(suite_id):
            run = reader(path)
            if run is not None:
                all_runs.append(run)
    all_runs.sort(key=lambda run: run.run_at or datetime.min.replace(tzinfo=UTC), reverse=True)

    latest_runs: list[QualityRunRead] = []
    for suite_id in SUITES:
        suite_runs = [run for run in all_runs if run.suite_id == suite_id]
        latest_runs.append(suite_runs[0] if suite_runs else _not_run(suite_id))

    saved_latest = [run for run in latest_runs if run.status != "not_run"]
    passed_count = sum(run.status == "passed" for run in saved_latest)
    if not saved_latest:
        overall: Literal["passed", "failed", "partial", "not_run"] = "not_run"
    elif any(run.status == "failed" for run in saved_latest):
        overall = "failed"
    elif len(saved_latest) < len(latest_runs):
        overall = "partial"
    else:
        overall = "passed"
    last_updated = max((run.run_at for run in all_runs if run.run_at), default=None)
    return QualityDashboardRead(
        overall_status=overall,
        total_suites=len(latest_runs),
        passing_suites=passed_count,
        saved_run_count=len(all_runs),
        last_updated=last_updated,
        latest_runs=latest_runs,
        recent_runs=all_runs[:10],
    )
