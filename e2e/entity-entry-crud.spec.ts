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

test("@crud @entity performs browser UI CRUD", async ({
  page,
  request,
}, testInfo) => {
  await page.goto("/ui/entities");
  await page.getByRole("link", { name: "新規モデルを作成" }).click();
  await page.getByPlaceholder("モデル名").fill("Browser Entity");
  await page.getByPlaceholder("備考").fill("created through browser");
  await page.getByRole("combobox", { name: "アイテム名の登録方法" }).click();
  await page.getByRole("option", { name: "UUIDに自動で設定" }).click();
  await page.getByPlaceholder("備考").press("Tab");
  await expect(page.getByRole("button", { name: "保存" })).toBeEnabled();
  await page.getByRole("button", { name: "保存" }).click();
  await expect(page).toHaveURL(/\/ui\/entities$/);
  await page.reload();

  let entityLink = page.getByText("Browser Entity", { exact: true });
  await expect(entityLink).toBeVisible();
  const created = (
    await (await request.get("/entity/api/v2")).json()
  ).results.find(({ name }: { name: string }) => name === "Browser Entity");
  expect(created).toBeDefined();

  const card = entityLink.locator(
    "xpath=ancestor::div[contains(@class, 'MuiCard-root')]",
  );
  await card.getByRole("button", { name: "モデルの操作" }).click();
  await page.getByText("編集", { exact: true }).click();
  await expect(page.getByPlaceholder("モデル名")).toHaveValue("Browser Entity");
  await page.getByPlaceholder("モデル名").fill("Browser Entity Updated");
  await page.getByPlaceholder("モデル名").press("Tab");
  const entriesLoaded = page.waitForResponse(
    (response) =>
      response.request().method() === "GET" &&
      response.url().includes(`/entity/api/v2/${created.id}/entries`),
  );
  await page.getByRole("button", { name: "保存" }).click();
  await entriesLoaded;
  await page.goto("/ui/entities");
  await page.reload();

  entityLink = page.getByText("Browser Entity Updated", { exact: true });
  await expect(entityLink).toBeVisible();
  const updatedCard = entityLink.locator(
    "xpath=ancestor::div[contains(@class, 'MuiCard-root')]",
  );
  await updatedCard.getByRole("button", { name: "モデルの操作" }).click();
  await page.getByText("削除", { exact: true }).click();
  await page.getByRole("button", { name: "Yes" }).click();
  await expect(entityLink).toHaveCount(0);
  expect((await request.get(`/entity/api/v2/${created.id}`)).status()).toBe(
    404,
  );

  await captureEvidence(page, testInfo, {
    name: "entity-crud",
    title: "Entity CRUD",
    note: "Created, read, updated, and deleted an entity through browser UI.",
  });
});

test("@crud @entry performs browser UI CRUD", async ({
  page,
  request,
}, testInfo) => {
  await page.goto("/ui/entities/1/entries");
  await page.getByRole("link", { name: "新規アイテムを作成" }).click();
  const name = page.locator("#entry-name");
  await name.fill("browser-entry");
  await name.press("Tab");
  await expect(page.getByRole("button", { name: "保存" })).toBeEnabled();
  await page.getByRole("button", { name: "保存" }).click();
  await expect(page).toHaveURL(/\/ui\/entities\/1\/entries$/);
  await page.reload();

  let entryLink = page.getByText("browser-entry", { exact: true });
  await expect(entryLink).toBeVisible();
  const created = (
    await (await request.get("/entity/api/v2/1/entries")).json()
  ).results.find(
    ({ name: entryName }: { name: string }) => entryName === "browser-entry",
  );
  expect(created).toBeDefined();

  await entryLink.click();
  await page.locator("#entryMenu").click();
  await page.getByText("編集", { exact: true }).click();
  await expect(page.locator("#entry-name")).toHaveValue("browser-entry");
  await page.locator("#entry-name").fill("browser-entry-updated");
  await page.locator("#entry-name").press("Tab");
  await page.getByRole("button", { name: "保存" }).click();
  await expect(page).toHaveURL(
    new RegExp(`/ui/entities/1/entries/${created.id}/details$`),
  );
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "browser-entry-updated" }),
  ).toBeVisible();

  await page.locator("#entryMenu").click();
  await page.getByText("削除", { exact: true }).click();
  await page.getByRole("button", { name: "Yes" }).click();
  await expect(page).toHaveURL(/\/ui\/entities\/1\/entries$/);
  await page.reload();
  entryLink = page.getByText("browser-entry-updated", { exact: true });
  await expect(entryLink).toHaveCount(0);
  expect((await request.get(`/entry/api/v2/${created.id}`)).status()).toBe(404);

  await captureEvidence(page, testInfo, {
    name: "entry-crud",
    title: "Entry CRUD",
    note: "Created, read, updated, and deleted an entry through browser UI.",
  });
});
