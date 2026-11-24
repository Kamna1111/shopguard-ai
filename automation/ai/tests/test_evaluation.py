"""Checks for the deterministic AI/RAG evaluation harness."""

import json
from pathlib import Path

from automation.ai.evaluate_rag import run_evaluation

from app.ai.providers import MockAIProvider

ROOT = Path(__file__).resolve().parents[3]


def test_golden_support_set_has_perfect_mock_baseline() -> None:
    golden_set = json.loads(
        (ROOT / "automation/ai/golden_data/support_questions.json").read_text(encoding="utf-8")
    )

    report = run_evaluation(golden_set, MockAIProvider())

    assert report["case_count"] == 6
    assert report["passed_count"] == 6
    assert report["mean_retrieval_precision"] == 1.0
    assert report["mean_retrieval_recall"] == 1.0
    assert report["answer_pass_rate"] == 1.0


def test_empty_golden_set_has_safe_zero_latency_metrics() -> None:
    report = run_evaluation([], MockAIProvider())

    assert report["pass_rate"] == 1.0
    assert report["latency_ms_p50"] == 0
    assert report["latency_ms_p95"] == 0
