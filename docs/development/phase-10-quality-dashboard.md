# Phase 10: quality dashboard

## What this phase does

The dashboard puts the latest saved quality results on one screen. Right now it shows two kinds of checks: the AI answer evaluation and the shop API speed test. It also shows a short history when those test commands save new runs.

## Why we added it

Before this phase, results were in separate files and Terminal output. The dashboard makes it easier to see whether the latest checks passed and compare earlier runs without opening every file.

## How to open it

1. In IntelliJ Terminal tab 1, start the API with `make api`.
2. In Terminal tab 2, start the website with `make web`.
3. Open `http://127.0.0.1:5173`.
4. Choose **Quality dashboard** in the shop's top menu.
5. Run `make ai-eval` or `make perf-smoke` in another Terminal tab, then press **Refresh results** on the dashboard.

The API speed test needs the API running. The AI evaluation command uses the local mock and does not need an AI key.

## Where the pieces are

- `apps/web/src/quality-dashboard.tsx` draws the dashboard screen.
- `apps/web/src/app.tsx` switches between the shop and dashboard pages.
- `apps/api/app/api/quality.py` provides the `GET /quality/summary` route.
- `apps/api/app/services/quality_dashboard.py` reads the saved result files and makes safe summary cards.
- `outputs/test-results/` holds the latest summaries and timestamped history copies.

The screen only shows counts, pass/fail status, times, and report file names. It does not show customer details or full AI questions and answers.

## What the numbers say

- **Passed:** the test met its checks and practice targets.
- **Failed:** at least one check or target failed.
- **Partial:** one type of test has a result, and another has not been run yet.
- **Not run:** there is no saved result file yet.

The first version covered AI evaluation and performance reports. Phase 12 extends it to browser, API, API component, and AI safety summaries too. See the [Phase 12 guide](phase-12-integration-reporting.md) for running those suites and making a combined report.
