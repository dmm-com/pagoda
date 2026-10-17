import { expect, test } from "@playwright/test";
import type { Locator } from "@playwright/test";

import {
  collectBrowserFailures,
  expectNoBrowserFailures,
  expectUiQualityGate,
} from "./browserQuality";
import { captureEvidence } from "./reportEvidence";

const failureMap = new WeakMap<object, string[]>();

test.use({ locale: "ja-JP" });

const expectSingleLineNotice = async (notice: Locator) => {
  const lineCount = await notice.locator("a").evaluate((link) => {
    const range = document.createRange();
    range.selectNodeContents(link);
    return range.getClientRects().length;
  });
  expect(lineCount).toBe(1);
};

test.beforeEach(async ({ page, request }, testInfo) => {
  expect((await request.post("/__e2e/reset")).status()).toBe(204);
  failureMap.set(testInfo, collectBrowserFailures(page));
});

test.afterEach(async ({ page }, testInfo) => {
  await expectUiQualityGate(page, testInfo);
  expectNoBrowserFailures(failureMap.get(testInfo) ?? []);
});

test("open model page reflects an ongoing change and its completion", async ({
  page,
  request,
}, testInfo) => {
  test.setTimeout(45_000);
  const entity = await (await request.get("/entity/api/v2/1")).json();
  let ongoing = true;

  await page.route(/\/entity\/api\/v2\/1\/?(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: { ...entity, has_ongoing_changes: ongoing },
    });
  });
  await page.route("**/job/api/v2/jobs*", async (route) => {
    await route.fulfill({
      json: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 55,
            user: "admin",
            text: "",
            status: ongoing ? 5 : 2,
            operation: 10,
            created_at: new Date().toISOString(),
            target: {
              id: 1,
              name: "Server",
              schema_id: null,
              schema_name: null,
            },
            passed_time: 10,
          },
        ],
      },
    });
  });

  await page.goto("/ui/entities/1/entries");
  const notice = page.getByRole("status");
  await expect(notice).toContainText("属性・設定を反映中");
  await expectSingleLineNotice(notice);
  await captureEvidence(page, testInfo, {
    name: "model-change-in-progress",
    title: "Model change in progress",
    note: "The page names the affected data and links to its job history.",
  });

  ongoing = false;
  await expect(notice).toHaveCount(0, { timeout: 25_000 });
  await captureEvidence(page, testInfo, {
    name: "model-change-complete",
    title: "Model change complete",
    note: "The notice disappears without a page reload.",
  });
});

test("open item page changes from processing to delay and timeout", async ({
  page,
  request,
}, testInfo) => {
  test.setTimeout(60_000);
  const entry = await (await request.get("/entry/api/v2/1")).json();
  let status = 5;
  let passedTime = 10;

  await page.route(/\/entry\/api\/v2\/1\/?(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: { ...entry, has_ongoing_changes: true },
    });
  });
  await page.route("**/job/api/v2/jobs*", async (route) => {
    await route.fulfill({
      json: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 56,
            user: "admin",
            text: "",
            status,
            operation: 2,
            created_at: new Date().toISOString(),
            target: {
              id: 1,
              name: "web-01",
              schema_id: 1,
              schema_name: "Server",
            },
            passed_time: passedTime,
          },
        ],
      },
    });
  });

  await page.goto("/ui/entities/1/entries/1/details");
  const notice = page.getByRole("status");
  await expect(notice).toContainText("値・検索結果を反映中");
  await expectSingleLineNotice(notice);
  await captureEvidence(page, testInfo, {
    name: "item-change-in-progress",
    title: "Item change in progress",
    note: "The notice names the data that may still be old.",
  });

  passedTime = 301;
  await expect(notice).toContainText("時間がかかっています", {
    timeout: 25_000,
  });
  await expectSingleLineNotice(notice);
  await captureEvidence(page, testInfo, {
    name: "item-change-slow",
    title: "Item change delayed",
    note: "The notice changes after five minutes of job time.",
  });

  status = 4;
  await expect(notice).toContainText("変更が完了していません", {
    timeout: 25_000,
  });
  await expectSingleLineNotice(notice);
  await captureEvidence(page, testInfo, {
    name: "item-change-timeout",
    title: "Item change timed out",
    note: "The page shows that the item change did not finish and links to its job history.",
  });
});
