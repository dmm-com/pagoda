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

test("@crud @user performs browser UI CRUD", async ({
  page,
  request,
}, testInfo) => {
  await page.goto("/ui/users");
  await page.getByRole("link", { name: "新規ユーザを登録" }).click();
  await page
    .getByPlaceholder("ユーザ名を入力してください")
    .fill("browser-user");
  await page
    .getByPlaceholder("メールアドレスを入力してください")
    .fill("browser-user@example.test");
  const password = page.getByPlaceholder("パスワードを入力してください");
  await password.fill("secret123");
  await password.press("Tab");
  await page.getByRole("button", { name: "保存" }).click();
  await expect(page).toHaveURL(/\/ui\/users$/);
  await page.reload();
  await expect(page.getByText("browser-user", { exact: true })).toBeVisible();
  const created = (
    await (await request.get("/user/api/v2")).json()
  ).results.find(
    ({ username }: { username: string }) => username === "browser-user",
  );
  await page.getByText("browser-user", { exact: true }).click();
  const username = page.getByPlaceholder("ユーザ名を入力してください");
  await expect(username).toHaveValue("browser-user");
  await username.fill("browser-user-updated");
  await username.press("Tab");
  await page.getByRole("button", { name: "保存" }).click();
  await page.reload();
  const updated = page.getByText("browser-user-updated", { exact: true });
  await expect(updated).toBeVisible();
  const card = updated.locator(
    "xpath=ancestor::div[contains(@class, 'MuiCard-root')]",
  );
  await card.getByRole("button").last().click();
  await page.getByText("削除", { exact: true }).click();
  await page.getByRole("button", { name: "Yes" }).click();
  await expect(updated).toHaveCount(0);
  expect((await request.get(`/user/api/v2/${created.id}`)).status()).toBe(404);
  await captureEvidence(page, testInfo, {
    name: "user-crud",
    title: "User CRUD",
    note: "Browser UI CRUD completed.",
  });
});

test("@crud @group performs browser UI CRUD", async ({
  page,
  request,
}, testInfo) => {
  await page.goto("/ui/groups");
  await page.getByRole("link", { name: "新規グループを作成" }).click();
  const input = page.getByPlaceholder("グループ名");
  await input.fill("Browser Group");
  await input.press("Tab");
  await page.getByRole("button", { name: "保存" }).click();
  await page.reload();
  const createdLink = page.getByText("Browser Group", { exact: true });
  await expect(createdLink).toBeVisible();
  const created = (
    await (await request.get("/group/api/v2/groups")).json()
  ).results.find(({ name }: { name: string }) => name === "Browser Group");
  await createdLink.click();
  await input.fill("Browser Group Updated");
  await input.press("Tab");
  await page.getByRole("button", { name: "保存" }).click();
  await page.reload();
  const updated = page.getByText("Browser Group Updated", { exact: true });
  const item = updated.locator("xpath=ancestor::li[1]");
  await item.getByRole("button").click();
  await page.getByText("削除", { exact: true }).click();
  await page.getByRole("button", { name: "Yes" }).click();
  await expect(updated).toHaveCount(0);
  expect(
    (await request.get(`/group/api/v2/groups/${created.id}`)).status(),
  ).toBe(404);
  await captureEvidence(page, testInfo, {
    name: "group-crud",
    title: "Group CRUD",
    note: "Browser UI CRUD completed.",
  });
});

test("@crud @role performs browser UI CRUD", async ({
  page,
  request,
}, testInfo) => {
  await page.goto("/ui/roles");
  await page.getByRole("link", { name: "新規ロールを作成" }).click();
  await page.getByPlaceholder("ロール名").fill("Browser Role");
  await page.getByPlaceholder("備考").fill("created through browser");
  const adminGroup = page.getByRole("row", { name: /管理者/ }).first();
  await adminGroup.getByRole("combobox").click();
  await page.getByRole("option", { name: "Engineering" }).click();
  await page.getByRole("button", { name: "保存" }).click();
  await page.reload();
  let row = page.getByRole("row").filter({ hasText: "Browser Role" });
  const created = (await (await request.get("/role/api/v2")).json()).find(
    ({ name }: { name: string }) => name === "Browser Role",
  );
  await row.getByRole("link", { name: "Browser Roleを編集" }).click();
  await page.getByPlaceholder("ロール名").fill("Browser Role Updated");
  await page.getByPlaceholder("備考").fill("updated through browser");
  await page.getByRole("button", { name: "保存" }).click();
  await page.reload();
  row = page.getByRole("row").filter({ hasText: "Browser Role Updated" });
  await expect(row).toContainText("updated through browser");
  await row.getByRole("button", { name: "Browser Role Updatedを削除" }).click();
  await page.getByRole("button", { name: "Yes" }).click();
  await expect(row).toHaveCount(0);
  expect((await request.get(`/role/api/v2/${created.id}`)).status()).toBe(404);
  await captureEvidence(page, testInfo, {
    name: "role-crud",
    title: "Role CRUD",
    note: "Browser UI CRUD completed.",
  });
});
