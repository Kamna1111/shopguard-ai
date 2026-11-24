# Phase 4: storefront and Playwright browser tests

## The idea in simple words

Phase 3 made the shop's back office: the API and database. Phase 4 gives it a small customer shop page and teaches an automated browser to use that page. Playwright acts like a customer clicking, typing, and checking what the page says.

The store page has product search, account registration and sign-in, a basket, checkout, order history, and cancellation. It uses the existing API; product and order rules still live in the backend.

## What the new folders do

```text
apps/web/
├── index.html                     # Browser page entry point
├── package.json                   # JavaScript libraries and commands
├── playwright.config.ts           # Browsers, retries, reports, server startup
├── vite.config.ts                 # React dev server and /api forwarding
├── src/
│   ├── main.tsx                   # Starts React
│   ├── storefront.tsx             # Product, account, basket, and order screen
│   └── style.css                  # Store appearance and phone layout
└── tests/
    ├── fixtures.ts                # Fresh test email and reusable page helper
    ├── pages/store-page.ts        # Common browser actions and selectors
    └── storefront.spec.ts         # Customer journeys and stock API check
```

`playwright.config.ts` tells Playwright where the shop is, which browser engines to use, where to save reports, and how to start the API and React development server when needed. On your computer, it reuses servers already running on the expected ports. In CI it starts fresh servers.

`tests/pages/store-page.ts` is a Page Object. It gives test code readable actions such as `register()` and `addFirstProduct()` instead of repeating low-level clicks in every test. `tests/fixtures.ts` gives each test a unique email, so tests do not collide with each other's accounts.

## Install once

Use IntelliJ's **Terminal** panel, at the project folder:

```bash
make web-install
make ui-browsers
```

`web-install` downloads the JavaScript tools. `ui-browsers` downloads Chromium, Firefox, and WebKit, the browser engines Playwright can control. If your network is restricted, the UI test may report that Chromium is missing; run `make ui-browsers` when browser downloads are allowed.

## Prepare the shop

The local PostgreSQL service and `shopguard` database must be ready, with the Phase 3 migration and sample products applied. If needed:

```bash
make db-migrate
make db-seed
```

The Playwright config starts the API and storefront for a test run if they are not already running. The API health check is at `http://127.0.0.1:8000/health`.

## Run your first browser checks

Start with Chromium:

```bash
make ui-test-chromium
```

The tests check product search, account registration, sign-in and sign-out, an invalid coupon, successful checkout followed by cancellation, and rejecting a basket quantity larger than stock.

The exact run time varies by computer. Playwright saves a screenshot, video, and trace when a browser test fails. These files are under `test-results/ui`; the HTML report is under `playwright-report`.

After Chromium works, run all configured browser engines:

```bash
make ui-test
```

To open the HTML report:

```bash
make ui-report
```

## Try the storefront yourself

```bash
make web
```

Open `http://127.0.0.1:5173`. Create a demo account using an email such as `learner@example.com` and a password of at least eight characters. Add a product, keep the sample `WELCOME10` discount code, and place a simulated order. No real payment details are collected. Stop the web server with **Control+C**.

## How a browser test works

For example, the checkout test opens the page, creates a fresh account, adds a product, submits the order, checks the confirmation, then cancels that order. The test uses labels and button names, like a person using the page. It waits for the expected page change instead of sleeping for a fixed number of seconds.

The insufficient-stock case uses Playwright's API request helper to send a quantity above the product's available stock. This checks the backend stock rule, while the other tests exercise the customer page.

## Common problems

| Message | Meaning and next step |
|---|---|
| `Executable doesn't exist` | Run `make ui-browsers`. |
| Connection refused on port 8000 | Start PostgreSQL, apply migrations, seed products, and retry. |
| Products are empty | Run `make db-seed`; confirm `/products` has sample rows. |
| Address already in use on port 4173 | Close the extra storefront process, or let Playwright reuse the server already open there. |
| Test says email already exists | Each test makes a new address. For manual testing, choose a different email. |

## Current limits

This is a learning storefront, not a production shop. It keeps the sign-in token in page memory, and has no password reset, address book, real payment, or accessibility audit. This phase focuses on the reusable Playwright setup and the requested customer journeys.
