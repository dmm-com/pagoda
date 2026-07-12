import { expect, test } from "@playwright/test";

import {
  collectBrowserFailures,
  expectNoBrowserFailures,
  expectUiQualityGate,
} from "./browserQuality";
import { captureEvidence } from "./reportEvidence";

const failureMap = new WeakMap<object, string[]>();

test.beforeEach(async ({ page, request }, testInfo) => {
  expect((await request.post("/__e2e/reset")).status()).toBe(204);
  failureMap.set(testInfo, collectBrowserFailures(page));
});

test.afterEach(async ({ page }, testInfo) => {
  await expectUiQualityGate(page, testInfo);
  expectNoBrowserFailures(failureMap.get(testInfo) ?? []);
});

test("@advanced-search creates, reads, updates, and clears search criteria", async ({
  page,
}, testInfo) => {
  await page.goto("/ui/advanced_search");

  const entitySelector = page.getByPlaceholder("モデルを選択");
  await entitySelector.click();
  await page.getByRole("option", { name: "Server" }).click();

  const attrSelector = page.getByPlaceholder("属性を選択");
  await attrSelector.click();
  await page.getByRole("option", { name: "すべて選択" }).click();
  await page.getByText("参照アイテムも含める").getByRole("checkbox").check();

  const search = page.getByRole("link", { name: "検索" });
  await expect(search).toBeEnabled();
  await search.click();
  await expect(page).toHaveURL(/\/ui\/advanced_search_result\?/);
  await expect(page.getByText("web-01", { exact: true })).toBeVisible();
  await expect(page.getByText("db-01", { exact: true })).toBeVisible();

  await page.goto("/ui/advanced_search");
  await entitySelector.click();
  await page.getByRole("option", { name: "Switch" }).click();
  await expect(page.getByRole("button", { name: "Switch" })).toBeVisible();

  await page.getByRole("button", { name: "Switch" }).getByTestId("CancelIcon").click();
  await expect(page.getByRole("link", { name: "検索" })).toHaveAttribute(
    "aria-disabled",
    "true",
  );

  await captureEvidence(page, testInfo, {
    name: "advanced-search-lifecycle",
    title: "Advanced Search Lifecycle",
    note: "Created, executed, updated, and cleared exhaustive search criteria.",
  });
});
