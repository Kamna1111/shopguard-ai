# Phase 3: the shop backend and PostgreSQL

## What we built

The backend is the part customers do not see directly. It follows shop rules, saves records in PostgreSQL, and answers requests from the future website and test tools.

The first working version supports:

- Customer registration and sign-in with hashed passwords and signed access tokens.
- Product listing, search, category filtering, sorting, and stock filtering.
- Administrator-only product creation and stock changes.
- A customer basket with quantity and stock checks.
- Checkout with a sample discount code, a configurable demonstration tax rate, and simulated payment reference.
- Order history and cancellation, including returning items to stock.
- Idempotency keys so retrying the same checkout request returns the existing order.

The tax rate is only a software demonstration setting. The payment reference begins with `SIM-`; the service does not connect to a payment provider or store card details.

## The easy way to remember the folders

Think of the backend as a small shop office:

- **API routes** are the front desk. They receive requests such as “show products” or “place my order.”
- **Schemas** are forms. They check that each request contains the right kind of information.
- **Models** are the tables in the office filing cabinet (PostgreSQL).
- **Services** are the shop rules. Checkout calculates totals and updates stock here.
- **Database code** opens and closes the connection to the filing cabinet.
- **Migrations** are numbered instructions that create or change database tables safely.

## Where the important logic lives

| File | What it does |
|---|---|
| `apps/api/app/main.py` | Creates the FastAPI app and connects all route groups. |
| `apps/api/app/core/config.py` | Reads private `.env` settings such as the database URL and demo tax rate. |
| `apps/api/app/core/database.py` | Opens a SQLAlchemy engine and provides one database session per request. |
| `apps/api/app/core/security.py` | Hashes passwords and creates time-limited sign-in tokens. |
| `apps/api/app/domain/models.py` | Defines PostgreSQL tables and data-integrity rules. |
| `apps/api/app/domain/schemas.py` | Validates incoming JSON and shapes outgoing responses. |
| `apps/api/app/api/auth.py` | Registration, login, and the signed-in account endpoint. |
| `apps/api/app/api/products.py` | Search, filtering, product details, and administrator product/stock changes. |
| `apps/api/app/api/cart.py` | Add, view, update, and remove basket items. |
| `apps/api/app/api/orders.py` | Checkout, order history, order details, and cancellation URLs. |
| `apps/api/app/services/checkout.py` | The important shopping rules: totals, discount, tax, stock locking, duplicate retries, and cancellation stock return. |
| `apps/api/migrations/versions/952aebf4c418_create_commerce_tables.py` | The first saved database-table change. |
| `apps/api/app/seed.py` | Adds three sample products and the `WELCOME10` discount code. |
| `apps/api/tests/test_shop_api.py` | Tests the API against the separate PostgreSQL test database. |

## One request, step by step

For checkout, the customer sends a JSON request to `POST /orders`.

1. `orders.py` receives the request and checks that the customer is signed in.
2. `schemas.py` checks the address, coupon, and idempotency key fields.
3. `checkout.py` loads the basket and locks the relevant stock rows in PostgreSQL.
4. The service checks available stock, calculates subtotal, discount, tax, and total, then creates an order.
5. It reduces stock and removes the basket rows in the same database transaction. If a check fails, it rolls back the transaction so stock and basket stay unchanged.
6. It returns an order confirmation with a simulated payment reference.

## Run it from IntelliJ

1. Confirm IntelliJ has the ShopGuard folder open. The folder is `/Users/Kamnaoza/Documents/Codex/2026-11-16/fr`.
2. Open **Terminal** at the bottom of IntelliJ. It should start in the project folder.
3. If this is a fresh copy, create `.env` from `.env.example`, install packages, migrate the database, and seed products:

   ```bash
   cp .env.example .env
   make setup-python
   createdb shopguard
   createdb shopguard_test
   make db-migrate
   make db-seed
   ```

   If the databases already exist, do not run `createdb` again.

4. Start the service:

   ```bash
   make api
   ```

5. Open `http://127.0.0.1:8000/docs`. This is FastAPI's interactive API page. Use the **Try it out** button on an endpoint to send a request.
6. Stop the service by clicking the Terminal and pressing `Control+C`.

## Try a customer order in the API docs

Use a demonstration address, not a real home address.

1. Send `POST /auth/register` with:

   ```json
   {
     "email": "buyer@example.com",
     "password": "safe-demo-pass-123"
   }
   ```

2. Send `POST /auth/login` with the same details. Copy the `access_token` from the result.
3. Select **Authorize** near the top of the docs page and paste the token. This lets the following calls act as that customer.
4. Send `GET /products`. Choose a product ID from the returned list.
5. Send `POST /cart/items` with that ID and a quantity, for example:

   ```json
   {
     "product_id": 1,
     "quantity": 2
   }
   ```

6. Send `GET /cart` to see the basket and subtotal.
7. Send `POST /orders`:

   ```json
   {
     "shipping_address": "123 Demo Road, Sample Town",
     "coupon_code": "WELCOME10",
     "idempotency_key": "my-first-order-0001"
   }
   ```

8. The response shows the order, discount, demo tax, total, and a `SIM-...` payment reference. `GET /orders` shows the customer's order history. `POST /orders/{order_id}/cancel` cancels a placed order and puts its items back in stock.

To try administrator product management locally, set both `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` in your private `.env`, then run `make db-seed`. Registering through the public API always creates a customer account; customers cannot grant themselves administrator access.

The example product IDs are selected from your `/products` response. Do not assume the IDs will always be the same on a different database.

## Run and understand the tests

In IntelliJ's built-in Terminal, run:

```bash
make test
```

The tests create fresh tables in `shopguard_test`, insert test-only records, call the API, and remove those tables when finished. They check sign-in, invalid inputs, product search, stock boundaries, checkout totals, invalid coupons, retry safety, admin access, order history, and cancellation.

You should see `13 passed`. The `shopguard` database is not used by this test setup.

## Useful commands and expected result

| Command | What should happen |
|---|---|
| `make db-migrate` | Alembic reports that it applied the `create commerce tables` migration. |
| `make db-seed` | Prints that demo products and `WELCOME10` are ready. Safe to repeat. |
| `make api` | Starts Uvicorn on `http://127.0.0.1:8000`. |
| `curl http://127.0.0.1:8000/health` | Returns `{"status":"ok","database":"ok"}` while the service is running. |
| `make test` | Runs setup and API checks on the isolated test database. |

## Current limits

This is the first backend slice. Password reset and saved-address management are not added yet. Logout for signed tokens means the client discards its token; there is no server-side token revocation list. The discount catalog is seeded with one sample code. Payments and tax are simulations. These limits keep the first backend learning step small and visible.
