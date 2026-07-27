import { expect, test } from "@playwright/test";

test("renders the project shell", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "AgentForge" })).toBeVisible();
});
