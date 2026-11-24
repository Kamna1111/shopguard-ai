import { expect, type Locator, type Page } from "@playwright/test";

export class StorePage {
  readonly searchBox: Locator;
  readonly basket: Locator;

  constructor(readonly page: Page) {
    this.searchBox = page.getByRole("textbox", { name: "Search products" });
    this.basket = page.locator("#basket");
  }

  async open() {
    await this.page.goto("/");
    await expect(this.page.getByRole("heading", { name: /Good things for/ })).toBeVisible();
  }

  async register(email: string, password = "shopguard-demo-123") {
    await this.page.getByLabel("Email address").fill(email);
    await this.page.getByLabel("Password").fill(password);
    await this.page.getByRole("button", { name: "Create account" }).click();
    await expect(this.page.getByTestId("signed-in-state")).toBeVisible();
  }

  async signIn(email: string, password: string) {
    await this.page.getByLabel("Email address").fill(email);
    await this.page.getByLabel("Password").fill(password);
    await this.page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(this.page.getByTestId("signed-in-state")).toBeVisible();
  }

  async addFirstProduct() {
    const firstCard = this.page.getByTestId("product-list").locator("article").first();
    const productName = (await firstCard.locator("h3").innerText()).trim();
    await firstCard.getByRole("button", { name: `Add ${productName} to basket` }).click();
    await expect(this.basket.getByText(productName, { exact: false })).toBeVisible();
    return productName;
  }

  async searchFor(text: string) {
    await this.searchBox.fill(text);
    await this.searchBox.press("Enter");
  }

  async filterByCategory(category: string) {
    await this.page.getByRole("combobox", { name: "Filter by category" }).selectOption(category);
  }
}
