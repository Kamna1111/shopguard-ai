"""Turn a JUnit XML test result into a small dashboard-friendly JSON summary."""

from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "test-results"
SUITES = {
    "project-tests": "Project and dashboard tests",
    "browser": "Browser journey checks",
    "api": "API behavior checks",
    "ai-security": "AI safety checks",
    "api-components": "API component checks",
}


def build_summary(suite_id: str, junit_file: Path) -> dict[str, object]:
    """Read JUnit XML and return a safe summary with counts only."""
    now = datetime.now(UTC)
    tests = failures = errors = skipped = 0
    report_created = junit_file.is_file()
    report_readable = report_created
    if report_created:
        try:
            root = ET.parse(junit_file).getroot()
            for case in root.iter("testcase"):
                tests += 1
                result = {child.tag for child in case}
                failures += int("failure" in result)
                errors += int("error" in result)
                skipped += int("skipped" in result)
        except ET.ParseError:
            report_readable = False

    passed = tests - failures - errors - skipped
    if not report_created:
        status = "not_run"
    elif report_readable and tests > 0 and failures == 0 and errors == 0:
        status = "passed"
    else:
        status = "failed"
    failed_total = failures + errors
    if report_created and report_readable:
        summary = f"{tests} checks; {passed} passed; {failed_total} failed; {skipped} skipped."
    elif report_created:
        summary = "The test report exists but could not be read. Check the test command output."
    else:
        summary = "No test report was created; this suite may not have run."

    stamp = now.strftime("%Y%m%dT%H%M%S.%fZ")
    name = SUITES[suite_id]
    if report_created:
        try:
            report_file = str(junit_file.relative_to(PROJECT_ROOT))
        except ValueError:
            report_file = junit_file.name
    else:
        report_file = None
    return {
        "suite_id": suite_id,
        "suite_name": name,
        "status": status,
        "summary": summary,
        "run_at": now.isoformat().replace("+00:00", "Z"),
        "test_count": tests,
        "passed_count": passed,
        "failed_count": failures,
        "error_count": errors,
        "skipped_count": skipped,
        "report_file": report_file,
        "run_id": f"{suite_id}-{stamp}",
    }


def write_summary(suite_id: str, junit_file: Path, output_dir: Path = OUTPUT_DIR) -> Path:
    """Save the current summary and a timestamped history copy."""
    summary = build_summary(suite_id, junit_file)
    output_dir.mkdir(parents=True, exist_ok=True)
    latest = output_dir / f"{suite_id}-latest.json"
    run_stamp = str(summary["run_id"]).removeprefix(f"{suite_id}-")
    archive = output_dir / f"{suite_id}-{run_stamp}.json"
    if junit_file.is_file():
        junit_archive = output_dir / f"{suite_id}-{run_stamp}-junit.xml"
        shutil.copy2(junit_file, junit_archive)
        try:
            summary["report_file"] = str(junit_archive.relative_to(PROJECT_ROOT))
        except ValueError:
            summary["report_file"] = junit_archive.name
    serialized = json.dumps(summary, indent=2) + "\n"
    latest.write_text(serialized, encoding="utf-8")
    archive.write_text(serialized, encoding="utf-8")
    return latest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite_id", choices=SUITES)
    parser.add_argument("junit_file", type=Path)
    args = parser.parse_args()
    junit_file = args.junit_file
    if not junit_file.is_absolute():
        junit_file = PROJECT_ROOT / junit_file
    print(f"Saved {args.suite_id} summary: {write_summary(args.suite_id, junit_file)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
