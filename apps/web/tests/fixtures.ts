import { test as base } from "@playwright/test";
import { StorePage } from "./pages/store-page";

type ShopFixtures = { store: StorePage; testEmail: string };

export const test = base.extend<ShopFixtures>({
  store: async ({ page }, use) => {
    await use(new StorePage(page));
  },
  testEmail: async ({}, use, testInfo) => {
    const uniquePart = `${Date.now()}-${testInfo.workerIndex}-${testInfo.retry}`;
    await use(`shopguard-${uniquePart}@example.com`);
  },
});

export { expect } from "@playwright/test";
