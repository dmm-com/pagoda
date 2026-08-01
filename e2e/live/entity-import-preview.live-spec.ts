import { expect, Page, test } from "@playwright/test";

import {
  captureEvidence,
  recordTestResult,
  resetE2eReport,
  writeE2eReport,
} from "../reportEvidence";

/**
 * Runs against a real Django server and a real database (see e2e/live/README.md),
 * so the preview is exercised end to end: real permissions, real validation, and
 * a real rollback. The mock-server suite in e2e/ cannot cover any of that.
 */

const username = process.env.E2E_USERNAME ?? "admin";
const password = process.env.E2E_PASSWORD ?? "admin";

// Names are unique per run so that a previous run cannot turn a "create" row
// into a duplicate-name error.
const runId = Date.now();
const NEW_MODEL = `e2e-preview-new-${runId}`;
const TARGET_MODEL = `e2e-preview-target-${runId}`;
const INITIAL_NOTE = "initial note";
const UPDATED_NOTE = "updated by the import preview e2e";

const login = async (page: Page) => {
  await page.goto("/auth/login/");
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.getByRole("button", { name: "Login" }).click();
  await page.waitForURL(/\/ui\//);
};

// The requests are issued from the page itself so that they carry the very same
// session and CSRF cookies the UI uses.
const apiGet = async <T>(page: Page, url: string): Promise<T> =>
  page.evaluate(async (target) => {
    const response = await fetch(target, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      throw new Error(`GET ${target} failed with ${response.status}`);
    }
    return response.json();
  }, url);

interface ModelListResponse {
  results: { id: number; name: string }[];
}

const postYaml = async (page: Page, url: string, body: string): Promise<void> =>
  page.evaluate(
    async ({ target, payload }) => {
      const csrfToken =
        document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/)?.[1] ?? "";
      const response = await fetch(target, {
        method: "POST",
        headers: {
          "Content-Type": "application/yaml",
          "X-CSRFToken": decodeURIComponent(csrfToken),
        },
        body: payload,
      });
      if (!response.ok) {
        throw new Error(
          `POST ${target} failed with ${response.status}: ${await response.text()}`,
        );
      }
    },
    { target: url, payload: body },
  );

const findModelId = async (page: Page, name: string): Promise<number> => {
  const found = await apiGet<ModelListResponse>(
    page,
    `/entity/api/v2/?search=${encodeURIComponent(name)}`,
  );
  const model = found.results.find((entity) => entity.name === name);
  expect(model, `model ${name} should exist`).toBeDefined();
  return model.id;
};

const getModelNote = async (page: Page, id: number): Promise<string> =>
  (await apiGet<{ note: string }>(page, `/entity/api/v2/${id}/`)).note;

test.beforeAll(() => {
  resetE2eReport();
});

test.afterAll(() => {
  writeE2eReport({
    title: "Pagoda live E2E report: model import preview",
    summary: [
      "The real frontend bundle ran against a real Django server and database.",
      "A model import file was previewed before being applied, over a generated dataset of ~60 models and ~1800 items.",
      "The preview ran as a background job: the request only started it, and the dialog polled until it finished.",
      "The preview reported a creation, a field-level update and a row the importer would otherwise drop silently.",
      "The database was verified to be untouched while the preview was on screen, and to match the preview after importing.",
    ],
  });
});

test.afterEach(async ({}, testInfo) => {
  recordTestResult(testInfo);
});

test("previews what a model import would change, and changes nothing until asked", async ({
  page,
}, testInfo) => {
  await login(page);

  // Seed a model to update, so the preview has a real update to report.
  await postYaml(
    page,
    "/entity/api/v2/import",
    [
      "Entity:",
      `- {created_user: ${username}, name: ${TARGET_MODEL}, note: ${INITIAL_NOTE}, status: 0}`,
      "EntityAttr: []",
    ].join("\n"),
  );
  const targetId = await findModelId(page, TARGET_MODEL);

  const importFile = [
    "Entity:",
    `- {created_user: ${username}, name: ${NEW_MODEL}, note: created by the preview e2e, status: 0}`,
    `- {created_user: ${username}, id: ${targetId}, name: ${TARGET_MODEL},` +
      ` note: ${UPDATED_NOTE}, status: 0}`,
    "",
    "EntityAttr:",
    `- {created_user: ${username}, entity: model-that-does-not-exist,` +
      " is_mandatory: '0', name: e2e-broken-attr, refer: '', type: 2}",
  ].join("\n");

  await page.goto("/ui/entities");
  await page.getByRole("button", { name: "インポート" }).first().click();
  await expect(page.getByText("モデルのインポート")).toBeVisible();

  await page.locator('input[type="file"]').setInputFiles({
    name: "entity-import-preview.yaml",
    mimeType: "application/yaml",
    buffer: Buffer.from(importFile, "utf-8"),
  });

  // Previewing is something the user opts into: both buttons are offered, and
  // "インポート" alone would import the file without ever building a preview.
  await expect(page.getByTestId("preview-import-file")).toBeEnabled();
  await captureEvidence(page, testInfo, {
    name: "entity-import-preview-optional",
    title: "Previewing is optional",
    note:
      "After choosing a file the dialog offers 変更内容を確認 next to インポート." +
      " Nothing is previewed unless the user asks for it, so a hurried import" +
      " stays a single click.",
  });

  await page.getByTestId("preview-import-file").click();
  // The preview runs as a job, so the dialog waits on it before showing rows.
  const preview = page.getByTestId("import-preview");
  await expect(preview).toBeVisible({ timeout: 60_000 });

  await expect(preview.getByText("新規作成 1")).toBeVisible();
  await expect(preview.getByText("更新 1")).toBeVisible();
  await expect(preview.getByText("エラー 1")).toBeVisible();

  // The new model, the field-level difference, and the row the importer would
  // silently drop must all be visible before anything is applied.
  await expect(
    preview.getByRole("cell", { name: NEW_MODEL, exact: true }),
  ).toBeVisible();
  await expect(
    preview.getByRole("cell", {
      name: `note: ${INITIAL_NOTE} → ${UPDATED_NOTE}`,
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    preview.getByRole("cell", { name: "e2e-broken-attr", exact: true }),
  ).toBeVisible();
  await expect(
    preview.getByRole("cell", {
      name: "failed to identify entity object",
      exact: true,
    }),
  ).toBeVisible();

  await captureEvidence(page, testInfo, {
    name: "entity-import-preview",
    title: "Model import preview",
    note:
      "The preview reports one creation, one field-level update and one row that the" +
      " importer would silently drop -- before any of it is applied.",
  });

  // Nothing has been written yet.
  expect(await getModelNote(page, targetId)).toBe(INITIAL_NOTE);
  const beforeImport = await apiGet<ModelListResponse>(
    page,
    `/entity/api/v2/?search=${encodeURIComponent(NEW_MODEL)}`,
  );
  expect(beforeImport.results).toHaveLength(0);

  // Importing after the preview applies exactly what was previewed. The form
  // reloads the page on success, so settle on a fresh one before querying.
  await page.getByRole("button", { name: "インポート" }).last().click();
  await page.goto(`/ui/entities?search=${encodeURIComponent("e2e-preview")}`);

  await expect
    .poll(async () => getModelNote(page, targetId), { timeout: 30_000 })
    .toBe(UPDATED_NOTE);
  await findModelId(page, NEW_MODEL);

  await captureEvidence(page, testInfo, {
    name: "entity-import-applied",
    title: "Model list after applying the previewed import",
    note: "The creation and the update the preview announced are now in place.",
  });
});
