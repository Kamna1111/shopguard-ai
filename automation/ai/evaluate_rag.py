"""Run the local golden-question evaluation for support retrieval and answers."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDEN_SET = PROJECT_ROOT / "automation/ai/golden_data/support_questions.json"
DEFAULT_REPORT = PROJECT_ROOT / "outputs/test-results/ai-evaluation-latest.json"

sys.path.insert(0, str(PROJECT_ROOT / "apps/api"))

from app.ai.providers import AIProvider, get_ai_provider  # noqa: E402
from app.ai.support import answer_question  # noqa: E402
from app.core.config import settings  # noqa: E402


def evaluate_case(case: dict[str, Any], provider: AIProvider) -> dict[str, Any]:
    """Compare one answer and its retrieved sources with its curated expectations."""
    started = time.perf_counter()
    answer, actual_sources = answer_question(case["question"], provider)
    latency_ms = round((time.perf_counter() - started) * 1000, 3)

    expected = set(case["expected_sources"])
    actual = set(actual_sources)
    overlap = expected & actual
    precision = len(overlap) / len(actual) if actual else float(not expected)
    recall = len(overlap) / len(expected) if expected else float(not actual)
    missing_phrases = [
        phrase
        for phrase in case["answer_must_include"]
        if phrase.casefold() not in answer.casefold()
    ]
    retrieval_pass = recall == 1.0 and precision == 1.0
    answer_pass = not missing_phrases
    return {
        "id": case["id"],
        "question": case["question"],
        "expected_sources": sorted(expected),
        "actual_sources": actual_sources,
        "retrieval_precision": round(precision, 3),
        "retrieval_recall": round(recall, 3),
        "answer_pass": answer_pass,
        "missing_answer_phrases": missing_phrases,
        "answer": answer,
        "latency_ms": latency_ms,
        "passed": retrieval_pass and answer_pass,
    }


def run_evaluation(golden_set: list[dict[str, Any]], provider: AIProvider) -> dict[str, Any]:
    """Run all golden examples and calculate retrieval, answer, and latency scores."""
    results = [evaluate_case(case, provider) for case in golden_set]
    latencies = [result["latency_ms"] for result in results]
    sorted_latencies = sorted(latencies)
    p95_index = max(0, int(len(sorted_latencies) * 0.95 + 0.999) - 1)
    return {
        "run_at": datetime.now(UTC).isoformat(),
        "provider": provider.name,
        "model": settings.openai_model if provider.name == "openai" else None,
        "case_count": len(results),
        "passed_count": sum(result["passed"] for result in results),
        "pass_rate": round(sum(result["passed"] for result in results) / len(results), 3)
        if results
        else 1.0,
        "mean_retrieval_precision": round(
            statistics.mean(result["retrieval_precision"] for result in results), 3
        )
        if results
        else 1.0,
        "mean_retrieval_recall": round(
            statistics.mean(result["retrieval_recall"] for result in results), 3
        )
        if results
        else 1.0,
        "answer_pass_rate": round(
            sum(result["answer_pass"] for result in results) / len(results), 3
        )
        if results
        else 1.0,
        "latency_ms_p50": round(statistics.median(latencies), 3) if latencies else 0,
        "latency_ms_p95": sorted_latencies[p95_index] if sorted_latencies else 0,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden-set", type=Path, default=DEFAULT_GOLDEN_SET)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--minimum-pass-rate", type=float, default=1.0)
    args = parser.parse_args()

    golden_set = json.loads(args.golden_set.read_text(encoding="utf-8"))
    report = run_evaluation(golden_set, get_ai_provider())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report_text = json.dumps(report, indent=2) + "\n"
    args.output.write_text(report_text, encoding="utf-8")
    run_stamp = datetime.fromisoformat(report["run_at"]).strftime("%Y%m%dT%H%M%S%fZ")
    history_report = args.output.parent / f"ai-evaluation-{run_stamp}.json"
    history_report.write_text(report_text, encoding="utf-8")

    print(
        f"AI evaluation: {report['passed_count']}/{report['case_count']} passed "
        f"({report['pass_rate']:.0%}); retrieval precision "
        f"{report['mean_retrieval_precision']:.0%}, recall "
        f"{report['mean_retrieval_recall']:.0%}; answer checks "
        f"{report['answer_pass_rate']:.0%}; p95 {report['latency_ms_p95']} ms"
    )
    print(f"Report saved to {args.output}")
    print(f"History copy saved to {history_report}")
    for result in report["results"]:
        marker = "PASS" if result["passed"] else "FAIL"
        print(f"{marker} {result['id']}: sources={result['actual_sources']}")
    return 0 if report["pass_rate"] >= args.minimum_pass_rate else 1


if __name__ == "__main__":
    raise SystemExit(main())
