# Phase 9: see how the shop handles visitors

## What happens in this phase?

We use a tool called k6 to act like several shoppers visiting the shop at once. It repeatedly opens the health page, product list, and product search. Then it measures how long the API takes and whether it returns errors.

The test only reads information. It does not create accounts, change stock, add basket items, or place orders.

## One-time setup

In IntelliJ's Terminal, install k6 once:

```bash
brew install k6
k6 version
```

Grafana's official k6 guide lists Homebrew as the macOS installation method: [Install k6](https://grafana.com/docs/k6/latest/set-up/install-k6/).

## Run the test

1. Make sure PostgreSQL is running and the project database is set up.
2. In one IntelliJ Terminal tab, start the API with `make api`. Keep that tab open.
3. In another tab, run `make perf-smoke` for a quick check with one pretend shopper for 10 seconds.
4. When that works, you can run `make perf-test` for five pretend shoppers for 30 seconds.
5. Open `outputs/test-results/performance-latest.json` in IntelliJ to see the saved results.

You can change the normal load from the Terminal too:

```bash
SHOPGUARD_LOAD_VUS=10 SHOPGUARD_LOAD_DURATION=1m make perf-test
```

That means 10 pretend shoppers for one minute. Start with the small smoke test before raising the numbers.

## How to read the result

- **Response time:** how long the API took to answer.
- **p95:** 95 out of 100 requests should finish faster than this time.
- **Failed requests:** requests that did not succeed.
- **Checks:** whether the response status and basic response shape were right.

The starter pass rules are: fewer than 1 in 100 requests fail, 95% finish within 800 milliseconds, and at least 99% of response checks pass. These are practice targets for this local project, not a promise about a real shop.

## Where the files are

- `automation/performance/shop-read-load.js` defines what the pretend shoppers do.
- `Makefile` defines `make perf-smoke` and `make perf-test`.
- `outputs/test-results/performance-latest.json` receives the latest result.

## Why this helps

A shop may work correctly for one person but slow down when many people visit together. This test helps us notice slow answers and errors before adding a dashboard or more features. The current test checks only the local shop API, not an internet shop or the AI model.
