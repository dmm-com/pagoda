import { expect, test } from "@playwright/test";

import {
  collectBrowserFailures,
  expectNoBrowserFailures,
  expectUiQualityGate,
} from "./browserQuality";
import {
  captureEvidence,
  recordTestResult,
  resetE2eReport,
  writeE2eReport,
} from "./reportEvidence";

const browserFailureMap = new WeakMap<object, string[]>();

const allAttributeNames = [
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
];

test.beforeAll(() => {
  resetE2eReport();
});

test.afterAll(() => {
  writeE2eReport();
});

test.beforeEach(async ({ page }, testInfo) => {
  browserFailureMap.set(testInfo, collectBrowserFailures(page));
  await page.addInitScript(() => {
    window.localStorage.setItem("e2e", "true");
  });
});

test.afterEach(async ({ page }, testInfo) => {
  const failures = browserFailureMap.get(testInfo) ?? [];
  try {
    await expectUiQualityGate(page, testInfo);
    expectNoBrowserFailures(failures);
  } finally {
    recordTestResult(testInfo);
  }
});

test("@smoke @dashboard renders dashboard cards", async ({
  page,
}, testInfo) => {
  await page.goto("/ui/");
  await expect(page.getByText("Operations")).toBeVisible();
  await expect(page.getByRole("link", { name: "Server" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Switch" })).toBeVisible();

  await captureEvidence(page, testInfo, {
    name: "dashboard",
    title: "Dashboard",
    note: "Dashboard category and model cards rendered from the mock category API.",
  });
});

test("@smoke @entry-list renders entries", async ({ page }, testInfo) => {
  await page.goto("/ui/entities/1/entries");
  await expect(page.getByRole("heading", { name: "Server" })).toBeVisible();
  await expect(page.getByRole("link", { name: "web-01" })).toBeVisible();
  await expect(page.getByRole("link", { name: "db-01" })).toBeVisible();

  await captureEvidence(page, testInfo, {
    name: "entry-list",
    title: "Entry List",
    note: "Entity-scoped entry list rendered with fixture entries.",
  });
});

test("@smoke @entry-detail renders attribute values", async ({
  page,
}, testInfo) => {
  await page.goto("/ui/entities/1/entries/1/details");
  await expect(page.getByRole("heading", { name: "web-01" })).toBeVisible();

  for (const attrName of allAttributeNames) {
    await expect(
      page.getByRole("cell", { name: attrName, exact: true }),
    ).toBeVisible();
  }

  await expect(page.getByText("web-01.example.test")).toBeVisible();
  await expect(page.getByText("switch-core-01", { exact: true })).toBeVisible();
  await expect(
    page.getByText("switch-backup-01", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("switch-uplink-01", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("switch-standby-01", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Runs the customer-facing web tier."),
  ).toBeVisible();
  await expect(page.locator('input[type="checkbox"]').first()).toBeChecked();
  await expect(page.getByText("SRE").first()).toBeVisible();
  await expect(page.getByText("Inventory Maintainer").first()).toBeVisible();
  await expect(page.getByText("web-primary")).toBeVisible();
  await expect(page.getByText("frontend-a")).toBeVisible();
  await expect(page.getByText("443")).toBeVisible();
  await expect(page.getByText("production")).toBeVisible();
  await expect(page.getByText("metrics")).toBeVisible();

  await captureEvidence(page, testInfo, {
    name: "entry-detail",
    title: "Entry Detail",
    note: "Entry detail rendered scalar, object, array-object, named-object, and array-named-object values.",
  });
});

test("@smoke @model-list renders models", async ({ page }, testInfo) => {
  await page.goto("/ui/entities");
  await expect(page.getByRole("heading", { name: "モデル一覧" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Server" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Switch" })).toBeVisible();

  await captureEvidence(page, testInfo, {
    name: "model-list",
    title: "Model List",
    note: "Model list rendered from the mock entity API.",
  });
});

test("@smoke @object-values renders object-like attribute values", async ({
  page,
}, testInfo) => {
  await page.goto("/ui/entities/1/entries/1/details");

  const expectedLinks = [
    ["switch-core-01", "/ui/entities/2/entries/20/details"],
    ["switch-backup-01", "/ui/entities/2/entries/21/details"],
    ["switch-uplink-01", "/ui/entities/2/entries/22/details"],
    ["switch-standby-01", "/ui/entities/2/entries/23/details"],
  ] as const;

  for (const [label, href] of expectedLinks) {
    await expect(
      page.getByRole("link", { name: label, exact: true }),
    ).toHaveAttribute("href", href);
  }

  await expect(page.getByText("uplink", { exact: true })).toBeVisible();
  await expect(page.getByText("standby", { exact: true })).toBeVisible();

  await captureEvidence(page, testInfo, {
    name: "object-like-attributes",
    title: "Object-like Attribute Values",
    note: "Object, array-object, named-object, and array-named-object values rendered as links to their entries.",
  });
});
