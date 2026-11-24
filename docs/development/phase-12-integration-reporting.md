# Phase 12: Integration, reporting, and documentation

Phase 12 connects the existing test suites to one reporting path. Python and Playwright tests write JUnit XML. A small reporting helper turns those files into safe JSON summaries and keeps a timestamped copy of each JUnit result. The quality API and dashboard read those summaries alongside the existing AI evaluation and k6 reports. A report command creates a Markdown summary, and GitHub Actions saves the detailed artifacts for each workflow run.

## Why this phase is useful

Each check used to leave its result in a different place: a Terminal, a Playwright HTML page, or a JSON file. This phase puts the latest result from each suite on the quality dashboard and makes a report that can be shared or reviewed later. A missing result is shown as not run, so it is not mistaken for a passing check.

## Suites shown

- Project and dashboard tests
- API component tests
- API checks through HTTP
- Browser journey checks
- AI safety checks
- AI answer evaluation
- API performance checks from k6

## Generate local results

Run the suites that fit the local setup:

```sh
make project-test
make api-component-test  # PostgreSQL must be running
make api                 # keep this Terminal open for HTTP tests
make api-test            # use another Terminal
make ai-security-test
make ai-eval
make perf-smoke           # k6 and the API must be running
make ui-test-chromium     # PostgreSQL must be running; Playwright starts the API and website
make quality-report
```

Before the API and browser checks, start PostgreSQL, then run `make db-migrate` and `make db-seed` once. The API must be running for `make api-test`; Playwright starts its own API and website for `make ui-test-chromium`.

The combined Markdown report is written to `docs/reports/quality-report-latest.md`. JSON summaries and JUnit files are written to `outputs/test-results/`. The report only includes counts and test status; it does not copy customer data or AI prompts into the dashboard.

After results have been saved, open the storefront, choose **Quality dashboard**, and press **Refresh results**. It reads the saved files through `GET /quality/summary`.

## GitHub Actions

On pushes and pull requests, the workflow runs project tests, API component tests, HTTP API tests, AI safety checks, AI answer evaluation, a Chromium browser journey, a web build, and Docker image builds. It creates the combined report even when a test step fails and uploads test artifacts to the workflow run. k6 performance checks remain a local/manual command so a load run is only started when requested.

## Main files

- `automation/reporting/normalize_junit.py` reads JUnit XML and saves a latest summary plus a dated copy.
- `automation/reporting/run_pytest_suite.py` runs a pytest suite and saves its JUnit and JSON outputs.
- `automation/reporting/build_quality_report.py` creates the Markdown report and a JSON dashboard snapshot.
- `apps/api/app/services/quality_dashboard.py` combines the saved suite summaries.
- `apps/web/src/quality-dashboard.tsx` displays the latest checks and recent history.
- `.github/workflows/quality.yml` runs the integrated checks and uploads their artifacts.

## In simple words

Each test makes a small score sheet. The reporting helper makes the score sheets look alike. The API gathers them, the dashboard shows them, and the Markdown report gives us a file to share.
