import { expect, test } from "@playwright/test";

import {
  collectBrowserFailures,
  expectNoBrowserFailures,
  expectUiQualityGate,
} from "./browserQuality";
import { captureEvidence } from "./reportEvidence";

// Controls are located by their Japanese labels.
test.use({ locale: "ja-JP" });

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
  // The display attribute picker of object attributes is a combobox sharing
  // the same placeholder; only the attribute name fields are counted here.
  const names = page.locator(
    'input[placeholder="属性名"]:not([role="combobox"])',
  );
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
  await expect(page.getByRole("button", { name: "選択肢を追加" })).toHaveCount(
    2,
  );

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

test("@attribute-types @entry loads stored values into the edit form", async ({
  page,
}, testInfo) => {
  // Regression: array fields used to insert placeholder rows while rendering,
  // which left the item name and array values empty on the edit page and
  // logged "Cannot update a component while rendering a different component".
  await page.goto("/ui/entities/1/entries/1/edit");

  await expect(page.locator("#entry-name")).toHaveValue("web-01");
  const rowOf = (attributeName: string) =>
    page.getByRole("row").filter({
      has: page.getByText(attributeName, { exact: true }),
    });
  const aliases = rowOf("aliases").locator("input");
  await expect(aliases).toHaveCount(2);
  await expect(aliases.nth(0)).toHaveValue("web-primary");
  await expect(aliases.nth(1)).toHaveValue("frontend-a");
  const ports = rowOf("ports").locator('input[type="number"]');
  await expect(ports).toHaveCount(2);
  await expect(ports.nth(0)).toHaveValue("80");
  await expect(ports.nth(1)).toHaveValue("443");
  await expect(
    rowOf("named_switches").locator('input[value="standby"]'),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "保存" })).toBeDisabled();

  await captureEvidence(page, testInfo, {
    name: "entry-edit-stored-values",
    title: "Entry Edit Stored Values",
    note: "Entry edit form loaded the stored name and array values without React render warnings.",
  });
});
