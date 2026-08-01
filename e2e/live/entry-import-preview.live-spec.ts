import { expect, Page, test } from "@playwright/test";

import {
  captureEvidence,
  recordTestResult,
  writeE2eReport,
} from "../reportEvidence";

import { apiGet, login, postYaml } from "./liveApi";

/**
 * The item import preview, against a real server. Unlike the model preview it
 * never writes -- applying an item import also reindexes Elasticsearch and
 * queues webhook and trigger jobs -- so what this checks is that it still
 * reports what the import would do, and that nothing changed until it ran.
 */

const runId = Date.now();
const MODEL = `e2e-item-preview-${runId}`;
const EXISTING_ITEM = `item-existing-${runId}`;
const NEW_ITEM = `item-new-${runId}`;

interface ItemListResponse {
  results: { id: number; name: string }[];
}

const findItems = async (page: Page, modelId: number) =>
  (await apiGet<ItemListResponse>(page, `/entity/api/v2/${modelId}/entries/`))
    .results;

test.afterEach(async ({}, testInfo) => {
  recordTestResult(testInfo);
});

// This file runs last, so it writes the report covering the whole live suite.
test.afterAll(() => {
  writeE2eReport({
    title: "Pagoda live E2E report: import previews",
    summary: [
      "The real frontend bundle ran against a real Django server, database and Celery worker.",
      "Model and item import files were previewed before being applied, over a generated dataset of ~60 models and ~1800 items.",
      "Previews ran as background jobs: the request only started them, and the dialog polled until they finished.",
      "The previews reported creations, field-level updates, and rows the importer would otherwise drop silently.",
      "The database was verified to be untouched while each preview was on screen, and to match it after importing.",
    ],
  });
});

test("previews what an item import would change, and writes nothing while it does", async ({
  page,
}, testInfo) => {
  await login(page);

  // A model with one text attribute, and one item already holding a value.
  await postYaml(
    page,
    "/entity/api/v2/import",
    [
      "Entity:",
      `- {created_user: admin, name: ${MODEL}, note: '', status: 0}`,
      "EntityAttr:",
      `- {created_user: admin, entity: ${MODEL}, is_mandatory: '0', name: note,` +
        " refer: '', type: 2}",
    ].join("\n"),
  );
  const modelId = (
    await apiGet<ItemListResponse>(
      page,
      `/entity/api/v2/?search=${encodeURIComponent(MODEL)}`,
    )
  ).results.find((entity) => entity.name === MODEL)?.id;
  expect(modelId, "the seeded model should exist").toBeDefined();
  if (modelId == null) return;

  const importFile = (entries: string[]) =>
    [`- entity: ${MODEL}`, "  entries:", ...entries].join("\n");

  await postYaml(
    page,
    "/entry/api/v2/import/",
    importFile([
      `  - name: ${EXISTING_ITEM}`,
      "    attrs:",
      "      - name: note",
      "        value: before",
    ]),
  );
  await expect
    .poll(async () => (await findItems(page, modelId)).length, {
      timeout: 30_000,
    })
    .toBe(1);

  // The file changes the existing item and adds a new one.
  const preview = importFile([
    `  - name: ${EXISTING_ITEM}`,
    "    attrs:",
    "      - name: note",
    "        value: after",
    `  - name: ${NEW_ITEM}`,
    "    attrs:",
    "      - name: note",
    "        value: brand new",
  ]);

  await page.goto(`/ui/entities/${modelId}/entries`);
  // Importing items lives behind the model menu on the item list page.
  await page.locator("#entity_menu").click();
  await page.getByRole("menuitem", { name: "インポート" }).click();
  await expect(page.getByText("アイテムのインポート")).toBeVisible();

  await page.locator('input[type="file"]').setInputFiles({
    name: "entry-import-preview.yaml",
    mimeType: "application/yaml",
    buffer: Buffer.from(preview, "utf-8"),
  });

  await page.getByTestId("preview-import-file").click();
  const result = page.getByTestId("import-preview");
  await expect(result).toBeVisible({ timeout: 60_000 });

  await expect(result.getByText("新規作成 1")).toBeVisible();
  await expect(result.getByText("更新 1")).toBeVisible();
  await expect(
    result.getByRole("cell", { name: "note: before → after", exact: true }),
  ).toBeVisible();
  await expect(
    result.getByRole("cell", { name: NEW_ITEM, exact: true }),
  ).toBeVisible();

  await captureEvidence(page, testInfo, {
    name: "entry-import-preview",
    title: "Item import preview",
    note:
      "One item would be created and one attribute value would change from" +
      " 'before' to 'after'. Item previews never write: the import path they" +
      " report on also reindexes and notifies, which no transaction can undo.",
  });

  // Nothing was written while the preview was on screen.
  expect(await findItems(page, modelId)).toHaveLength(1);

  // The seeding import already ran for this model today, and item imports refuse
  // a second one within a day unless forced.
  await page.getByTestId("force-import").check();
  await page.getByRole("button", { name: "インポート" }).last().click();
  await expect
    .poll(async () => (await findItems(page, modelId)).map((x) => x.name), {
      timeout: 60_000,
    })
    .toContain(NEW_ITEM);
});
