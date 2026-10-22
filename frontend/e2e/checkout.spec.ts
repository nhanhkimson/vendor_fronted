import { expect, test } from "@playwright/test";

test("Maya checks out a linen bag", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: /Jess A/ }).waitFor();
  await page.getByRole("button", { name: /Maya R/ }).click();
  await page.waitForURL(/\/account/);
  await page.goto("/products/P12");
  await page.getByRole("button", { name: "Add to cart" }).click();
  await page.goto("/checkout");
  await expect(page.getByText(/Total \$/)).toBeVisible();
  await page.getByRole("button", { name: "Pay and place the order" }).click();
  await page.waitForURL(/\/account\/orders\/O-/);
  await expect(page.getByRole("heading", { name: /O-/ })).toBeVisible();
});
