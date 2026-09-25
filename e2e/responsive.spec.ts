import { expect, Page, test } from "@playwright/test";

import {
  collectBrowserFailures,
  expectNoBrowserFailures,
  expectUiQualityGate,
} from "./browserQuality";
import { captureEvidence } from "./reportEvidence";

// Breakpoints from frontend/src/Theme.tsx.
const SM = 600;
const MD = 900;
const LG = 1200;

const viewports = [
  { name: "phone", width: 375, height: 667 },
  { name: "small-tablet", width: 600, height: 960 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "tablet-landscape", width: 900, height: 700 },
  { name: "laptop", width: 1024, height: 768 },
  { name: "desktop", width: 1280, height: 800 },
  { name: "wide-desktop", width: 1920, height: 1080 },
];

const failureMap = new WeakMap<object, string[]>();

test.beforeEach(async ({ page, request }, testInfo) => {
  expect((await request.post("/__e2e/reset")).status()).toBe(204);
  failureMap.set(testInfo, collectBrowserFailures(page));
});

test.afterEach(async ({ page }, testInfo) => {
  await expectUiQualityGate(page, testInfo);
  expectNoBrowserFailures(failureMap.get(testInfo) ?? []);
});

const toolbar = (page: Page) => page.locator("header .MuiToolbar-root");

const navToggle = (page: Page) =>
  page.getByRole("button", { name: "Open navigation menu" });

const expectHeaderFitsInOneRow = async (page: Page) => {
  const box = await toolbar(page).boundingBox();
  expect(box?.height).toBe(56);
  const overflow = await toolbar(page).evaluate(
    (element) => element.scrollWidth - element.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);

  // The toolbar has a fixed height, so labels wrapping onto extra lines spill
  // out of it without changing its size. Every visible item must stay inside.
  const spilled = await toolbar(page).evaluate((element) => {
    const bounds = element.getBoundingClientRect();
    return [...element.querySelectorAll("a, button, input, p")]
      .map((item) => ({ item, rect: item.getBoundingClientRect() }))
      .filter(
        ({ rect }) =>
          rect.width > 0 &&
          rect.height > 0 &&
          (rect.top < bounds.top - 1 || rect.bottom > bounds.bottom + 1),
      )
      .map(({ item, rect }) => ({
        text: item.textContent?.trim() || item.tagName,
        top: rect.top,
        bottom: rect.bottom,
      }));
  });
  expect(spilled).toEqual([]);
};

// Number of distinct columns the dashboard category cards are laid out in.
const categoryColumnCount = async (page: Page) => {
  const lefts = await page
    .locator(".MuiGrid2-container > .MuiGrid2-root")
    .evaluateAll((elements) =>
      elements.map((element) =>
        Math.round(element.getBoundingClientRect().left),
      ),
    );
  return new Set(lefts).size;
};

for (const viewport of viewports) {
  test.describe(`@responsive ${viewport.name} (${viewport.width}px)`, () => {
    test.use({
      viewport: { width: viewport.width, height: viewport.height },
    });

    test("dashboard keeps every control reachable", async ({
      page,
    }, testInfo) => {
      await page.goto("/ui/");
      await expect(page.getByText("Operations")).toBeVisible();
      await expectHeaderFitsInOneRow(page);

      const expectedColumns =
        viewport.width >= MD ? 3 : viewport.width >= SM ? 2 : 1;
      expect(await categoryColumnCount(page)).toBe(expectedColumns);

      const createButton = page.getByRole("link", {
        name: "新規カテゴリを作成",
      });
      await expect(createButton).toBeVisible();
      // The label must stay on one line instead of wrapping per character.
      expect((await createButton.boundingBox())?.height).toBe(48);

      const headerSearch = page
        .locator("header")
        .getByPlaceholder("Search", { exact: true });
      if (viewport.width >= SM) {
        await expect(headerSearch).toBeVisible();
      } else {
        await expect(headerSearch).toBeHidden();
      }

      if (viewport.width >= MD) {
        await expect(navToggle(page)).toBeHidden();
        for (const name of ["Categories", "Entities", "Advanced Search"]) {
          await expect(
            page.locator("header").getByRole("link", { name }),
          ).toBeVisible();
        }
      } else {
        await expect(
          page.locator("header").getByRole("link", { name: "Categories" }),
        ).toBeHidden();
        await navToggle(page).click();
        const drawer = page.locator("#nav-drawer");
        for (const name of [
          "Categories",
          "Entities",
          "Advanced Search",
          "Manage users",
          "Manage groups",
          "Manage roles",
          "Manage triggers",
        ]) {
          await expect(drawer.getByRole("link", { name })).toBeVisible();
        }
        const drawerSearch = drawer.getByPlaceholder("Search", {
          exact: true,
        });
        if (viewport.width >= SM) {
          await expect(drawerSearch).toBeHidden();
        } else {
          await expect(drawerSearch).toBeVisible();
        }
        await expectUiQualityGate(page, testInfo);
        await captureEvidence(page, testInfo, {
          name: `responsive-${viewport.name}-menu`,
          title: `Navigation drawer at ${viewport.width}px`,
          note: "Header navigation collapsed into the menu button.",
        });
        await page.keyboard.press("Escape");
        await expect(drawer).toBeHidden();
      }

      await captureEvidence(page, testInfo, {
        name: `responsive-${viewport.name}`,
        title: `Dashboard at ${viewport.width}px`,
        note: `Dashboard at ${viewport.width}x${viewport.height} with ${expectedColumns} category column(s).`,
      });
    });

    test("simple search results fit the viewport", async ({ page }) => {
      await page.goto("/ui/?simple_search_query=web");
      await expect(page.getByRole("link", { name: "web-02" })).toBeVisible();
      await expectHeaderFitsInOneRow(page);
    });
  });
}

test.describe("@responsive navigation drawer", () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test("navigates and closes the drawer", async ({ page }) => {
    await page.goto("/ui/");
    await navToggle(page).click();
    const drawer = page.locator("#nav-drawer");
    await drawer.getByRole("link", { name: "Entities" }).click();
    await expect(page).toHaveURL(/\/ui\/entities$/);
    await expect(drawer).toBeHidden();
    await expect(page.getByRole("progressbar")).toHaveCount(0);
    // Only the dashboard is responsive so far; the model list page still
    // clips controls on phones, so run the shared gate at desktop width.
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test("searches entries from the drawer", async ({ page }) => {
    await page.goto("/ui/");
    await navToggle(page).click();
    const drawer = page.locator("#nav-drawer");
    await drawer.getByPlaceholder("Search", { exact: true }).fill("web");
    await drawer.getByPlaceholder("Search", { exact: true }).press("Enter");
    await expect(page).toHaveURL(/simple_search_query=web/);
    await expect(drawer).toBeHidden();
    await expect(page.getByRole("link", { name: "web-02" })).toBeVisible();
  });
});

// Deployments usually show Japanese labels, extra header menus and the link to
// the previous UI, all of which widen the header compared to the fixture.
const useProductionLikeHeader = async (page: Page, title = "Pagoda") => {
  await page.route("**/ui/", async (route) => {
    const response = await route.fetch();
    const body = (await response.text())
      .replace('title: "Pagoda"', `title: "${title}"`)
      .replace("legacyUiDisabled: true", "legacyUiDisabled: false")
      .replace(
        "extendedHeaderMenus: []",
        `extendedHeaderMenus: [
          { name: "外部ツール", children: [{ name: "Grafana", url: "/grafana" }] },
          { name: "ドキュメント", children: [{ name: "手順書", url: "/docs" }] },
        ]`,
      );
    await route.fulfill({ response, body });
  });
};

test.describe("@responsive production-like header", () => {
  test.use({ locale: "ja-JP" });

  for (const viewport of viewports) {
    test(`keeps the header usable at ${viewport.width}px`, async ({
      page,
    }, testInfo) => {
      await useProductionLikeHeader(page);
      await page.setViewportSize(viewport);
      await page.goto("/ui/");
      await expect(page.getByText("Operations")).toBeVisible();
      // On desktop the header is intentionally left as it was, and with this
      // many menus its labels already wrapped onto two lines before
      // responsive support. Only the widths the responsive rules cover are
      // required to keep everything in one row.
      if (viewport.width < LG) {
        await expectHeaderFitsInOneRow(page);
      }
      await expectUiQualityGate(page, testInfo);
      await captureEvidence(page, testInfo, {
        name: `responsive-production-like-${viewport.name}`,
        title: `Production-like header at ${viewport.width}px`,
        note: "Japanese labels, extended menus and the previous UI link.",
      });
    });
  }

  // Desktop widths keep the original header untouched, so only the widths
  // where the responsive rules apply are expected to absorb a long title.
  for (const viewport of viewports.filter(({ width }) => width < LG)) {
    test(`truncates a long site title at ${viewport.width}px`, async ({
      page,
    }, testInfo) => {
      await useProductionLikeHeader(page, "Pagoda Inventory Production");
      await page.setViewportSize(viewport);
      await page.goto("/ui/");
      await expect(page.getByText("Operations")).toBeVisible();
      await expectHeaderFitsInOneRow(page);
      await expectUiQualityGate(page, testInfo);
    });
  }
});

test.describe("@responsive drawer on resize", () => {
  test("closes when the window becomes wide", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/ui/");
    await navToggle(page).click();
    await expect(page.locator("#nav-drawer")).toBeVisible();

    await page.setViewportSize({ width: 1280, height: 800 });
    await expect(page.locator("#nav-drawer")).toBeHidden();
  });
});

test.describe("@responsive desktop layout contract", () => {
  // These values are the desktop layout before responsive support was added.
  // They must not change, so that existing PC users see the same screen.
  for (const width of [LG, 1280, 1920]) {
    test(`keeps the desktop layout at ${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      await page.goto("/ui/");
      await expect(page.getByText("Operations")).toBeVisible();

      const toolbarBox = await toolbar(page).boundingBox();
      expect(toolbarBox?.width).toBe(LG);
      expect(toolbarBox?.height).toBe(56);
      await expect(navToggle(page)).toBeHidden();

      const headerSearchBox = await page
        .locator("header")
        .getByPlaceholder("Search", { exact: true })
        .locator("xpath=ancestor::div[contains(@class, 'MuiTextField-root')]")
        .boundingBox();
      expect(headerSearchBox?.width).toBe(240);

      const filterBox = await page
        .getByPlaceholder("カテゴリを絞り込む")
        .locator("xpath=ancestor::div[contains(@class, 'MuiTextField-root')]")
        .boundingBox();
      expect(filterBox?.width).toBe(600);

      const createBox = await page
        .getByRole("link", { name: "新規カテゴリを作成" })
        .boundingBox();
      // The create button stays on the same row as the filter box.
      expect(createBox?.y).toBe(filterBox?.y);

      expect(await categoryColumnCount(page)).toBe(3);
    });
  }
});
