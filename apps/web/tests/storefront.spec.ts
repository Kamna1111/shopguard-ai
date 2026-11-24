import { test, expect } from "./fixtures";

const demoPassword = "shopguard-demo-123";

test("customer can find a product by name", async ({ store }) => {
  await store.open();
  await expect(store.page.getByRole("heading", { name: "Trail Bottle" })).toBeVisible();
  await store.searchFor("Trail Bottle");
  await expect(store.page.getByTestId("product-list").locator("article")).toHaveCount(1);
  await expect(store.page.getByRole("heading", { name: "Trail Bottle" })).toBeVisible();
});

test("customer can filter and sort the product collection", async ({ store }) => {
  await store.open();
  await store.filterByCategory("Home");
  await expect(store.page.getByTestId("product-list").locator("article")).toHaveCount(1);
  await expect(store.page.getByRole("heading", { name: "Desk Lamp" })).toBeVisible();
  await store.filterByCategory("");
  await store.page.getByRole("combobox", { name: "Sort products" }).selectOption("price_asc");
  await expect(store.page.getByTestId("product-list").locator("article h3").first()).toHaveText("Travel Mug");
});

test("customer can create an account and sign out", async ({ store, testEmail }) => {
  await store.open();
  await store.register(testEmail);
  await expect(store.page.getByText("You’re signed in and ready to shop.")).toBeVisible();
  await store.page.getByRole("button", { name: "Sign out" }).click();
  await expect(store.page.getByRole("button", { name: "Sign in", exact: true })).toBeVisible();
  await expect(store.page.getByRole("status")).toContainText("You are signed out.");
});

test("customer can sign in to an existing account", async ({ store, testEmail }) => {
  await store.open();
  await store.register(testEmail, demoPassword);
  await store.page.getByRole("button", { name: "Sign out" }).click();
  await store.signIn(testEmail, demoPassword);
});

test("customer can change and remove an item in the basket", async ({ store, testEmail }) => {
  await store.open();
  await store.register(testEmail);
  const productName = await store.addFirstProduct();
  await store.basket.getByRole("button", { name: `Increase ${productName} quantity` }).click();
  await expect(store.basket.getByText("× 2")).toBeVisible();
  await store.basket.getByRole("button", { name: `Decrease ${productName} quantity` }).click();
  await store.basket.getByRole("button", { name: `Decrease ${productName} quantity` }).click();
  await expect(store.page.getByTestId("empty-basket")).toBeVisible();
});

test("invalid discount keeps the customer basket intact", async ({ store, testEmail }) => {
  await store.open();
  await store.register(testEmail);
  await store.addFirstProduct();
  await store.page.getByRole("textbox", { name: "Discount code" }).fill("NOT-A-REAL-CODE");
  await store.page.getByRole("button", { name: "Continue to checkout" }).click();
  await expect(store.page.getByRole("alert")).toContainText("discount code is not valid");
  await expect(store.basket.locator(".basket-line")).toHaveCount(1);
});

test("customer can place an order and cancel it", async ({ store, testEmail }) => {
  await store.open();
  await store.register(testEmail);
  const productName = await store.addFirstProduct();
  await store.page.getByRole("button", { name: "Continue to checkout" }).click();
  await expect(store.page.getByRole("status")).toContainText("placed successfully");
  const order = store.page.getByTestId("order-card").filter({ hasText: productName }).first();
  await expect(order).toContainText("placed");
  await order.getByRole("button", { name: "Cancel order" }).click();
  await expect(store.page.getByRole("status")).toContainText("returned to stock");
  await expect(order).toContainText("cancelled");
});

test("API rejects a basket quantity above available stock", async ({ request }) => {
  const email = `stock-check-${Date.now()}@example.com`;
  const registration = await request.post("http://127.0.0.1:8000/auth/register", {
    data: { email, password: demoPassword },
  });
  expect(registration.status()).toBe(201);
  const login = await request.post("http://127.0.0.1:8000/auth/login", {
    data: { email, password: demoPassword },
  });
  const { access_token: token } = await login.json();
  const productsResponse = await request.get("http://127.0.0.1:8000/products");
  const products = await productsResponse.json();
  const product = products.find((candidate: { available_quantity: number }) => candidate.available_quantity > 0);
  expect(product).toBeTruthy();

  const response = await request.post("http://127.0.0.1:8000/cart/items", {
    headers: { Authorization: `Bearer ${token}` },
    data: { product_id: product.id, quantity: 50 },
  });
  expect(response.status()).toBe(409);
  await expect(response.json()).resolves.toMatchObject({ detail: "There is not enough stock for that quantity." });
});
