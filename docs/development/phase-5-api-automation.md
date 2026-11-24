# Phase 5: Python API automation

## The idea in simple words

Phase 4 taught an automated browser to shop through the website. Phase 5 sends requests straight to the API, like another program would. That lets us check the shop's rules without clicking through the screen.

The app's own tests use FastAPI's built-in test client. These new tests use the popular **Requests** library over HTTP, so they behave more like an outside service checking the running shop.

## What the new folders do

```text
automation/api/
├── clients/
│   └── shop_api.py             # Shared Requests session, auth header, timeout, logs
├── schemas/
│   └── openapi_contract.py     # Checks response JSON using /openapi.json
└── tests/
    ├── conftest.py             # Server URL, API client, user, read-only DB connection
    ├── test_health_and_contract.py # Health, timing, products, contract, bad inputs
    ├── test_auth_and_access.py # Sign-in, invalid data, customer/admin rules
    └── test_cart_and_orders.py # Basket, stock, coupon, checkout, retry, cancel
```

`ShopApiClient` is the common helper. A test calls `api.get()` or `api.post()`; the helper consistently adds JSON headers, applies a timeout, attaches a sign-in token when provided, and logs method, route, status code, and time taken. It does not print passwords or tokens.

`validate_openapi_response()` reads the API's own `/openapi.json` contract and checks that a product response has the documented fields and types. If someone changes the response shape by accident, the contract test can catch it.

The `customer` fixture creates a unique email and signs in a customer for each test. A fixture is setup code Pytest reuses automatically. The database fixture is read-only and is used only to verify that checkout really saved an order and its item. These tests do not clear the shop database; they use distinct test accounts, remove basket items, and cancel successful test orders to restore stock.

## Run it from IntelliJ

1. Open the project in IntelliJ and open **Terminal**.
2. Start the database-backed API in one terminal and leave it open:

   ```bash
   make api
   ```

3. In a second Terminal tab, run:

   ```bash
   make api-test
   ```

The API URL defaults to `http://127.0.0.1:8000`. You can change it for another test server by setting `SHOPGUARD_API_URL`, for example:

```bash
SHOPGUARD_API_URL=http://127.0.0.1:8001 make api-test
```

## What the tests check

| Test area | Example thing it checks |
|---|---|
| Health and speed | Database is ready; local health request completes within the simple 2 second smoke-test limit. This is one request, not load testing. |
| API contract | Product list matches the live OpenAPI response description. |
| Products | Category filter and price sorting work; unknown product returns 404; too-long search returns 422. |
| Accounts | Registration and sign-in work; duplicate registration and bad/missing tokens are rejected. |
| Permissions | A customer cannot create an administrator product. |
| Basket | Add, read, change, remove; negative quantities and too much stock are rejected. |
| Checkout | Invalid discount does not empty the basket; a valid coupon produces an order. |
| Retry safety | Sending the same checkout key twice returns the same order, not a second purchase. |
| Cancellation | A placed order can be cancelled once, and stock returns to the product. |
| Database check | A read-only SQL query confirms checkout saved the expected order and item. |

Expected result is `13 passed`. Exact request times depend on your computer and whether the server is already warm. The tests print timings so you can compare requests; performance testing with many simultaneous customers is Phase 9.

## How to read a failed test

- `ConnectionError` means the API is not running or `SHOPGUARD_API_URL` points to the wrong place.
- `404` on `/products` or `500` can mean the API database is not ready. Check `make api`, run `make db-migrate`, then run `make db-seed`.
- `OpenAPI schema` failure means the response shape does not match the contract currently served by the API. Check the failing field and compare it with `apps/api/app/domain/schemas.py`.
- `409` is often a correct shop rule, such as stock being too low. The tests assert the expected status and error message.
- A database connection error means `.env` or `DATABASE_URL` does not point to the same local PostgreSQL database used by the API.

For one manual request, run `curl -i http://127.0.0.1:8000/products`. The status and JSON are the API response. The request logs are printed by the Python client during `make api-test`, while server access logs appear in the Terminal running `make api`.

## Common mistakes and interview practice

- Do not hard-code a product ID. Ask `GET /products` for a product, then use its returned ID.
- Do not check only that the server returned `200`. Also check important response fields and values.
- Do not print passwords or access tokens in logs. The shared client logs only method, route, status, and elapsed time.
- Keep API tests separate from browser tests: API tests are quicker and show backend rule failures directly; browser tests confirm a user's screen and clicks.

Questions you can practice answering:

1. What is the difference between an API test and an end-to-end browser test?
2. Why does a reusable API client help keep a test suite maintainable?
3. What does a JSON Schema or OpenAPI contract check catch that a status-code check might miss?
4. Why does checkout use an idempotency key, and how does this suite verify retry behavior?
5. How is a response-time smoke check different from a load test?

## Current limits

The API test suite is meant for a local learning database and creates customer rows that it cannot delete through the shop API. It never drops tables or removes existing accounts. Successful test orders are cancelled to restore product stock. Direct database checks use a read-only connection. A separate disposable CI database and automatic teardown will be added with the CI work.
