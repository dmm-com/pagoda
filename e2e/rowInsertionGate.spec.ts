import { expect, test } from "@playwright/test";

import {
  collectBrowserFailures,
  expectNoBrowserFailures,
  expectUiQualityGate,
  pageScrollWidth,
} from "./browserQuality";
import {
  captureEvidence,
  recordTestResult,
  resetE2eReport,
  writeE2eReport,
} from "./reportEvidence";

/**
 * Ad-hoc E2E gate for the row-insertion affordance rework.
 *
 * Scenario tags let the gate be grown in stages while every stage stays green:
 *   @gate1  behaviour of the append row and the insertion band
 *   @gate2  affordance separation, per-surface coverage, accessible names
 *   @gate3  nested lists, keyboard operation, narrow viewport
 */

// The bundle picks its UI language from navigator.languages.
test.use({ locale: "ja-JP" });

const ALIASES_ATTR = 23;

const ENTRY_EDIT = "/ui/entities/1/entries/1/edit";
const ENTITY_EDIT = "/ui/entities/1";
const TRIGGER_EDIT = "/ui/triggers/1";

const browserFailureMap = new WeakMap<object, string[]>();
/**
 * Tests that assert layout themselves instead of the global checks. The app has
 * a pre-existing ~1200px minimum content width, so pages do not fit a 1024px
 * viewport before or after this change; the test compares against a baseline
 * screen instead of asserting an absolute width.
 */
const selfMeasuredWidth = new WeakSet<object>();

const rowOf = (
  page: import("@playwright/test").Page,
  listId: string,
  index: number,
) => page.locator(`[data-list-id="${listId}"][data-row-index="${index}"]`);

const valuesIn = async (
  page: import("@playwright/test").Page,
  listId: string,
) =>
  page
    .locator(`[data-list-id="${listId}"] input`)
    .evaluateAll((elements) =>
      (elements as HTMLInputElement[]).map((element) => element.value),
    );

test.beforeAll(() => {
  resetE2eReport();
});

test.afterAll(() => {
  writeE2eReport({
    title: "Pagoda row-insertion affordance rework — E2E gate",
    summary: [
      "The real frontend bundle was booted in Chromium against the mock API server.",
      "Entry array attributes (string / number / named object), entity attributes, isolation rules, trigger conditions and trigger actions were exercised.",
      "Insertion bands were verified to land on the boundary they are drawn on, and the append row was verified to append at the end with focus moved into the new row.",
      "Every stage also checks browser console errors, page errors, failed requests, critical axe violations, horizontal overflow and off-screen controls.",
    ],
  });
});

test.beforeEach(async ({ page }, testInfo) => {
  browserFailureMap.set(testInfo, collectBrowserFailures(page));
});

test.afterEach(async ({ page }, testInfo) => {
  const failures = browserFailureMap.get(testInfo) ?? [];
  try {
    await expectUiQualityGate(page, testInfo, {
      skipLayoutChecks: selfMeasuredWidth.has(testInfo),
    });
    expectNoBrowserFailures(failures);
  } finally {
    recordTestResult(testInfo);
  }
});

// ---------------------------------------------------------------- gate 1 ---

test("@gate1 entry array attribute appends at the end and focuses the new row", async ({
  page,
}, testInfo) => {
  await page.goto(ENTRY_EDIT);

  const listId = `array-string-${ALIASES_ATTR}`;
  await expect(rowOf(page, listId, 0)).toBeVisible();
  expect(await valuesIn(page, listId)).toEqual(["web-primary", "frontend-a"]);

  await page.getByTestId(`append-row-${ALIASES_ATTR}`).click();

  // Appended at the END, not after an arbitrary row.
  expect(await valuesIn(page, listId)).toEqual([
    "web-primary",
    "frontend-a",
    "",
  ]);

  // The new row is focused so the user can type immediately.
  await expect(rowOf(page, listId, 2).locator("input")).toBeFocused();
  await page.keyboard.type("inserted-at-end");

  await captureEvidence(page, testInfo, {
    name: "gate1-append-row",
    title: "Append row adds at the end and focuses the new input",
    note: 'Entry edit / aliases (array_string). The "＋ 値を追加" control is the only place that appends; the new row is appended last and receives focus so typing continues without a second click.',
    locator: page.locator("tr", { hasText: "aliases" }).first(),
  });
});

test("@gate1 insertion band inserts exactly on the boundary it is drawn on", async ({
  page,
}, testInfo) => {
  await page.goto(ENTRY_EDIT);

  const listId = `array-string-${ALIASES_ATTR}`;
  await expect(rowOf(page, listId, 0)).toBeVisible();
  expect(await valuesIn(page, listId)).toEqual(["web-primary", "frontend-a"]);

  // The band drawn above the 1st row is index 0, the one between row 1 and 2
  // is index 1. Clicking it must insert *there*, not "somewhere after a row".
  await page.getByTestId(`insert-band-${ALIASES_ATTR}-0`).click();

  await expect(rowOf(page, listId, 2)).toBeVisible();
  expect(await valuesIn(page, listId)).toEqual([
    "",
    "web-primary",
    "frontend-a",
  ]);
  await expect(rowOf(page, listId, 0).locator("input")).toBeFocused();
  await page.keyboard.type("inserted-at-top");

  await page.getByTestId(`insert-band-${ALIASES_ATTR}-2`).click();

  await expect(rowOf(page, listId, 3)).toBeVisible();
  expect(await valuesIn(page, listId)).toEqual([
    "inserted-at-top",
    "web-primary",
    "",
    "frontend-a",
  ]);
  await expect(rowOf(page, listId, 2).locator("input")).toBeFocused();
  await page.keyboard.type("inserted-middle");

  expect(await valuesIn(page, listId)).toEqual([
    "inserted-at-top",
    "web-primary",
    "inserted-middle",
    "frontend-a",
  ]);

  await captureEvidence(page, testInfo, {
    name: "gate1-insert-band",
    title: "Insertion band inserts at the drawn boundary",
    note: "Two insertions via the band: one above the first row and one between row 1 and row 2. Values stay in the expected order, which proves the insertion index matches the pointer position rather than the row the control belongs to.",
    locator: page.locator("tr", { hasText: "aliases" }).first(),
  });
});

test("@gate1 isolation rules render a visible append row when empty", async ({
  page,
}, testInfo) => {
  await page.goto(ENTITY_EDIT);

  const append = page.getByTestId("append-row-isolation-rule");
  await append.scrollIntoViewIfNeeded();
  await expect(append).toBeVisible();
  await expect(append).toContainText("設定を追加");

  await append.click();

  await expect(rowOf(page, "isolation-rules", 0)).toBeVisible();
  // The nested condition list starts empty but offers its own append control.
  await expect(page.getByTestId("append-isolation-condition-0")).toBeVisible();

  const table = page.locator("#table_isolation_rules_list");
  await captureEvidence(page, testInfo, {
    name: "gate1-isolation-empty",
    title: "Isolation rules: empty state is one labelled append row",
    note: "The former empty state was a lone unlabelled ＋ inside a blank table row. It is now a labelled append row, and the nested condition list shows its own append control.",
    locator: table,
  });
});

test("@gate1 whole screens keep their hierarchy", async ({
  page,
}, testInfo) => {
  await page.goto(ENTRY_EDIT);
  await expect(page.getByTestId(`append-row-${ALIASES_ATTR}`)).toBeVisible();
  await captureEvidence(page, testInfo, {
    name: "gate1-entry-edit-full",
    title: "Entry edit — full screen",
    note: "Array attributes (aliases / named_switches / ports) now read as lists with a divider-shaped insert control between rows and a labelled append row at the end.",
  });

  await page.goto(ENTITY_EDIT);
  await expect(page.getByTestId("append-row-attribute")).toBeVisible();
  await captureEvidence(page, testInfo, {
    name: "gate1-entity-edit-full",
    title: "Entity edit — full screen",
    note: "The 追加 column is gone from the attribute table; the isolation-rules table and the webhook table end with labelled append rows.",
  });

  await page.goto(TRIGGER_EDIT);
  await expect(page.getByTestId("append-row-condition")).toBeVisible();
  await captureEvidence(page, testInfo, {
    name: "gate1-trigger-edit-full",
    title: "Trigger edit — full screen",
    note: "Conditions and actions both expose per-boundary bands plus one append row; nested action values have their own append control.",
  });
});

// ---------------------------------------------------------------- gate 2 ---

test("@gate2 rows no longer expose a per-row plus button", async ({
  page,
}, testInfo) => {
  await page.goto(ENTRY_EDIT);

  const listId = `array-string-${ALIASES_ATTR}`;
  await expect(rowOf(page, listId, 0)).toBeVisible();
  await expect(rowOf(page, listId, 1)).toBeVisible();
  for (const index of [0, 1]) {
    const buttons = rowOf(page, listId, index).locator("button");
    // Only the delete button remains inside the row.
    await expect(buttons).toHaveCount(1);
    await expect(buttons.first()).toHaveAttribute(
      "aria-label",
      new RegExp(`${index + 1}行目を削除`),
    );
  }

  await captureEvidence(page, testInfo, {
    name: "gate2-row-actions",
    title: "Row-level actions are delete-only",
    note: "Each array row keeps a single, labelled delete control. The insertion affordance moved out of the row and onto the boundary, so a row no longer owns an action whose effect happens elsewhere.",
    locator: page.locator("tr", { hasText: "aliases" }).first(),
  });
});

test("@gate2 trigger conditions insert on the boundary", async ({
  page,
}, testInfo) => {
  await page.goto(TRIGGER_EDIT);

  const listId = "trigger-conditions";
  const rows = page.locator(`[data-list-id="${listId}"]`);
  await expect(rows).toHaveCount(3);

  const textboxes = rows.getByRole("textbox");
  await expect(textboxes).toHaveCount(1);
  expect(await textboxes.first().inputValue()).toBe("web");

  // Insert above the 2nd condition: the new empty condition becomes row 2 and
  // the previous row 2 moves down.
  await page.getByTestId("insert-band-condition-1").click();

  await expect(rows).toHaveCount(4);
  await expect(rows.nth(2).getByRole("combobox").first()).toHaveText(
    /backup_switches/,
  );
  await expect(page.getByTestId("append-row-condition")).toBeVisible();

  await captureEvidence(page, testInfo, {
    name: "gate2-trigger-conditions",
    title: "Trigger conditions: boundaries carry the insert affordance",
    note: "A band sits between every pair of conditions and one labelled append row closes the table. The delete column no longer competes with a per-row ＋.",
    locator: page.locator("table").first(),
  });
});

test("@gate2 entity attributes insert on the boundary", async ({
  page,
}, testInfo) => {
  await page.goto(ENTITY_EDIT);

  const listId = "entity-attributes";
  await expect(page.locator("#table_attribute_list")).toBeVisible();
  const rows = page.locator(`[data-list-id="${listId}"]`);
  await expect(rows.first()).toBeVisible();
  const before = await rows.count();
  expect(before).toBeGreaterThan(1);

  const nameAt = async (index: number) =>
    rowOf(page, listId, index).locator("input").first().inputValue();
  expect(await nameAt(1)).toBe("primary_switch");

  await page.getByTestId("insert-band-attribute-1").click();

  await expect(rows).toHaveCount(before + 1);
  expect(await nameAt(1)).toBe("");
  expect(await nameAt(2)).toBe("primary_switch");
  await expect(rowOf(page, listId, 1).locator("input").first()).toBeFocused();

  await captureEvidence(page, testInfo, {
    name: "gate2-entity-attributes",
    title: "Entity attributes: insertion band and append row",
    note: "The entity attribute table lost its 追加 column. A band above each row inserts at that position and a labelled append row closes the table; the 並び替え column keeps working for reordering.",
    locator: page.locator("#table_attribute_list"),
  });
});

test("@gate2 every insertion control has an accessible name", async ({
  page,
}) => {
  await page.goto(ENTRY_EDIT);
  const listId = `array-string-${ALIASES_ATTR}`;

  // Accessible names include the attribute name, so repeated lists stay
  // distinguishable for screen reader users.
  await expect(
    page.getByRole("button", {
      name: "aliasesの1行目の前に値を追加",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "aliasesの2行目の前に値を追加",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByTestId(`append-row-${ALIASES_ATTR}`),
  ).toHaveAccessibleName("aliasesに値を追加");
  await expect(rowOf(page, listId, 0).getByRole("button")).toHaveAccessibleName(
    "1行目を削除",
  );
  expect(await page.locator("#add_button, #del_button").count()).toBe(0);
});

// ---------------------------------------------------------------- gate 3 ---

test("@gate3 trigger action values append into their own action only", async ({
  page,
}, testInfo) => {
  await page.goto(TRIGGER_EDIT);

  const actions = page.locator(`[data-list-id="trigger-actions"]`);
  await expect(actions).toHaveCount(3);

  const valueAppendForAliases = page.getByTestId("append-action-value-1");
  await valueAppendForAliases.scrollIntoViewIfNeeded();
  const valuesBefore = await page
    .locator(`[data-list-id="action-values-1"] input`)
    .count();

  await valueAppendForAliases.click();

  await expect(
    page.locator(`[data-list-id="action-values-1"] input`),
  ).toHaveCount(valuesBefore + 1);
  // Other actions are untouched.
  await expect(page.locator(`[data-list-id="action-values-2"]`)).toHaveCount(1);
  // Single-value action types keep exactly one input and no append control.
  await expect(page.locator(`[data-list-id="action-values-0"]`)).toHaveCount(1);
  await expect(page.getByTestId("append-action-value-0")).toHaveCount(0);
  await expect(page.getByTestId("append-action-value-2")).toHaveCount(0);

  await captureEvidence(page, testInfo, {
    name: "gate3-trigger-actions",
    title: "Trigger actions: outer rows and nested values are separated",
    note: "Action rows use bands plus a labelled append row; the nested value lists use their own append control, so an insertion can never be confused with the scope it belongs to.",
    locator: page.locator("table").nth(1),
  });
});

test("@gate3 insertion bands are keyboard operable", async ({ page }) => {
  await page.goto(ENTRY_EDIT);
  const listId = `array-string-${ALIASES_ATTR}`;

  const band = page.getByTestId(`insert-band-${ALIASES_ATTR}-1`);
  await band.focus();
  await expect(band).toBeFocused();
  await page.keyboard.press("Enter");

  expect(await valuesIn(page, listId)).toEqual([
    "web-primary",
    "",
    "frontend-a",
  ]);
  await expect(rowOf(page, listId, 1).locator("input")).toBeFocused();
});

test("@gate4 the gap affordance stays hidden until hovered", async ({
  page,
}, testInfo) => {
  await page.goto(TRIGGER_EDIT);
  const rows = page.locator('[data-list-id="trigger-conditions"]');
  await expect(rows.first()).toBeVisible();

  const band = page.getByTestId("insert-band-condition-1");
  const lineOpacity = () =>
    band.evaluate((el) => getComputedStyle(el, "::before").opacity);
  const chipOpacity = () =>
    band
      .locator("span")
      .first()
      .evaluate((el) => getComputedStyle(el).opacity);

  const table = page.locator("table").first();
  await captureEvidence(page, testInfo, {
    name: "gate4-gap-idle",
    title: "Gap affordance at rest",
    note: "No rules are drawn between rows, so a long list stays quiet. Every gap still carries a reachable control.",
    locator: table,
  });

  // Nothing is drawn between rows until the pointer reaches the gap.
  expect(await lineOpacity()).toBe("0");
  expect(await chipOpacity()).toBe("0");

  await band.hover();
  await captureEvidence(page, testInfo, {
    name: "gate4-gap-hover",
    title: "Gap affordance on hover",
    note: "Hovering the gap between two conditions reveals a thin line with a small plus, Jira-style, and clicking inserts exactly there.",
    locator: table,
  });
  await expect.poll(lineOpacity).toBe("1");
  await expect.poll(chipOpacity).toBe("1");

  // The revealed gap still inserts exactly where it is drawn.
  const comboboxes = rows.getByRole("combobox");
  const before = await comboboxes.count();
  await band.click();
  await expect(comboboxes).toHaveCount(before + 1);
});

test("@gate4 the append control reads as the last row", async ({
  page,
}, testInfo) => {
  await page.goto(TRIGGER_EDIT);
  const rows = page.locator('[data-list-id="trigger-conditions"]');
  await expect(rows.first()).toBeVisible();

  const appendRow = page.locator('tr[data-append-row="true"]').first();
  const appendButton = page.getByTestId("append-row-condition");
  await expect(appendButton).toBeVisible();

  const contentBox = await rows.first().boundingBox();
  const appendBox = await appendRow.boundingBox();
  expect(contentBox).not.toBeNull();
  expect(appendBox).not.toBeNull();

  // Same order of height as a data row, so it reads as the next row rather
  // than as a floating button.
  expect(
    Math.abs((appendBox?.height ?? 0) - (contentBox?.height ?? 0)),
  ).toBeLessThan(16);

  // And it really is the last row of the table body.
  const lastRowBox = await rows.last().boundingBox();
  expect(appendBox?.y ?? 0).toBeGreaterThan(lastRowBox?.y ?? 0);

  await captureEvidence(page, testInfo, {
    name: "gate4-append-row",
    title: "Append control is rendered as the last row",
    note: "The append control keeps the table row height and border and highlights as a whole row, so it reads as the next empty row instead of a button bolted onto the end.",
    locator: page.locator("table").first(),
  });
});

test("@gate3 narrow viewport does not widen the layout further", async ({
  page,
}, testInfo) => {
  selfMeasuredWidth.add(testInfo);
  await page.setViewportSize({ width: 1024, height: 900 });

  // The form screens have a pre-existing ~1200px minimum content width: the
  // same value was measured on the pre-change build, so 1200 is the ceiling
  // this change must not exceed.
  const PRE_EXISTING_MIN_CONTENT_WIDTH = 1200;

  await page.goto(ENTRY_EDIT);
  const appendRow = page.getByTestId(`append-row-${ALIASES_ATTR}`);
  await appendRow.scrollIntoViewIfNeeded();
  await expect(appendRow).toBeVisible();
  const band = page.getByTestId(`insert-band-${ALIASES_ATTR}-0`);
  await band.scrollIntoViewIfNeeded();
  await expect(band).toBeInViewport();
  expect(await pageScrollWidth(page)).toBeLessThanOrEqual(
    PRE_EXISTING_MIN_CONTENT_WIDTH,
  );

  await page.goto(ENTITY_EDIT);
  await expect(page.getByTestId("append-row-attribute")).toBeVisible();
  expect(await pageScrollWidth(page)).toBeLessThanOrEqual(
    PRE_EXISTING_MIN_CONTENT_WIDTH,
  );

  await page.goto(TRIGGER_EDIT);
  await expect(page.getByTestId("append-row-condition")).toBeVisible();
  expect(await pageScrollWidth(page)).toBeLessThanOrEqual(
    PRE_EXISTING_MIN_CONTENT_WIDTH,
  );
});
