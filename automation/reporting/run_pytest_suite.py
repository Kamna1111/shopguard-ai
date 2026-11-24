"""Run one pytest suite, save JUnit XML, and normalize its dashboard summary."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from automation.reporting.normalize_junit import OUTPUT_DIR, SUITES, write_summary  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite_id", choices=SUITES)
    parser.add_argument("tests", nargs="+", help="Test files or folders to run")
    args, pytest_args = parser.parse_known_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    junit_file = OUTPUT_DIR / f"{args.suite_id}-junit.xml"
    command = [
        sys.executable,
        "-m",
        "pytest",
        *args.tests,
        *pytest_args,
        f"--junitxml={junit_file}",
    ]
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    write_summary(args.suite_id, junit_file)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
