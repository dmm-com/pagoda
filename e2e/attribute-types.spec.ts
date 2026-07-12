import { expect, test } from "@playwright/test";

import {
  collectBrowserFailures,
  expectNoBrowserFailures,
  expectUiQualityGate,
} from "./browserQuality";
import { captureEvidence } from "./reportEvidence";

const attributeNames = [
  "hostname",
  "primary_switch",
  "backup_switches",
  "named_switch",
  "named_switches",
  "description",
  "is_virtual",
  "owner_group",
  "installed_on",
  "owner_role",
  "last_seen_at",
  "rack_units",
  "aliases",
  "maintenance_groups",
  "support_roles",
  "ports",
  "environment",
  "capabilities",
] as const;

const failureMap = new WeakMap<object, string[]>();

test.beforeEach(async ({ page, request }, testInfo) => {
  expect((await request.post("/__e2e/reset")).status()).toBe(204);
  failureMap.set(testInfo, collectBrowserFailures(page));
});

test.afterEach(async ({ page }, testInfo) => {
  await expectUiQualityGate(page, testInfo);
  expectNoBrowserFailures(failureMap.get(testInfo) ?? []);
});

test("@attribute-types @entity renders all 18 types in the entity editor", async ({
  page,
}, testInfo) => {
  await page.goto("/ui/entities/1");
  const names = page.getByPlaceholder("属性名");
  await expect(names).toHaveCount(attributeNames.length);
  expect(
    await names.evaluateAll((elements) =>
      elements.map((element) => (element as HTMLInputElement).value),
    ),
  ).toEqual([...attributeNames]);
  await expect(page.locator("#attr_type")).toHaveCount(attributeNames.length);
  for (const objectAttribute of [
    "primary_switch",
    "backup_switches",
    "named_switch",
    "named_switches",
  ]) {
    await expect(
      page
        .getByRole("row")
        .filter({
          has: page.locator(
            `input[placeholder="属性名"][value="${objectAttribute}"]`,
          ),
        })
        .getByPlaceholder("モデルを選択"),
    ).toBeVisible();
  }
  await expect(page.getByRole("button", { name: "選択肢を追加" })).toHaveCount(2);

  await captureEvidence(page, testInfo, {
    name: "entity-all-attribute-types",
    title: "Entity All Attribute Types",
    note: "Entity editor rendered all 18 supported attribute definitions.",
  });
});

test("@attribute-types @entry renders an editable control for all 18 types", async ({
  page,
}, testInfo) => {
  await page.goto("/ui/entities/1/entries/new");

  for (const attributeName of attributeNames) {
    const row = page.getByRole("row").filter({
      has: page.getByText(attributeName, { exact: true }),
    });
    await expect(row).toBeVisible();
    await expect(
      row.locator('input, textarea, [role="combobox"]').first(),
    ).toBeVisible();
  }

  await page
    .getByRole("row")
    .filter({ has: page.getByText("hostname", { exact: true }) })
    .locator("input")
    .fill("typed.example.test");
  await page
    .getByRole("row")
    .filter({ has: page.getByText("rack_units", { exact: true }) })
    .locator('input[type="number"]')
    .fill("42");
  await page
    .getByRole("row")
    .filter({ has: page.getByText("is_virtual", { exact: true }) })
    .getByRole("checkbox")
    .check();
  await page
    .getByRole("row")
    .filter({ has: page.getByText("environment", { exact: true }) })
    .getByRole("combobox")
    .click();
  await page.getByRole("option", { name: "production" }).click();

  await captureEvidence(page, testInfo, {
    name: "entry-all-attribute-types",
    title: "Entry All Attribute Types",
    note: "Entry form rendered controls for all 18 types and accepted representative values.",
  });
});
