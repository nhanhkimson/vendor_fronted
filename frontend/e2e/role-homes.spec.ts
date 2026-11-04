import { expect, test } from "@playwright/test";

const ROLES = [
  { label: "Customer", name: "Maya R.", path: /\/account/ },
  { label: "Seller", name: "Jess A.", path: /\/seller/ },
  { label: "Admin", name: "Ava K.", path: /\/admin/ },
  { label: "Support", name: "Lin S.", path: /\/admin/ },
  { label: "Super Admin", name: "Daniel O.", path: /\/admin/ },
] as const;

test("guide page loads", async ({ page }) => {
  await page.goto("/guide");
  await expect(page.getByRole("heading").first()).toBeVisible();
  await expect(page).toHaveURL(/\/guide/);
});

test("theme toggle switches dark class", async ({ page }) => {
  await page.goto("/");
  const html = page.locator("html");
  const themeBtn = page.getByRole("button", { name: /Switch to (dark|light) mode/i });
  await expect(themeBtn).toBeVisible();
  const wasDark = (await html.getAttribute("class"))?.includes("dark") ?? false;
  if (wasDark) {
    await page.getByRole("button", { name: /Switch to light mode/i }).click();
    await expect(html).not.toHaveClass(/dark/);
    await page.getByRole("button", { name: /Switch to dark mode/i }).click();
    await expect(html).toHaveClass(/dark/);
  } else {
    await themeBtn.click();
    await expect(html).toHaveClass(/dark/);
    await page.getByRole("button", { name: /Switch to light mode/i }).click();
    await expect(html).not.toHaveClass(/dark/);
  }
});

for (const role of ROLES) {
  test(`login lands ${role.label} on home`, async ({ page }) => {
    await page.goto("/login");
    await page.locator("#role").click();
    await page.getByRole("option", { name: role.label, exact: true }).click();
    await page.getByRole("button", { name: `Sign in as ${role.name}` }).click();
    await page.waitForURL(role.path);
    await expect(page).toHaveURL(role.path);
  });
}
