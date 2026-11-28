import { expect, type Page, test } from "@playwright/test";

import {
  collectBrowserFailures,
  expectNoBrowserFailures,
} from "./browserQuality";

test.use({ locale: "ja-JP" });

const percent = { query: "100%", name: "Capacity 100%", id: 1 };
const literal = {
  query: "日本語 + %2f%25",
  name: "Literal percent escapes",
  id: 2,
};
const pastedUrl = "/ui/entities?query=100%25&page=1";

function searchBox(page: Page) {
  return page.getByPlaceholder("モデルを絞り込む");
}

async function expectFilteredList(page: Page, filter: typeof percent) {
  await expect(searchBox(page)).toHaveValue(filter.query);
  await expect(
    page.getByRole("link", { name: filter.name, exact: true }),
  ).toBeVisible();
}

test("list search URLs preserve search text across tabs and browser history", async ({
  context,
  page,
}) => {
  // Only an exact API search term returns the corresponding fixture.
  await context.route(
    (url) => url.pathname === "/entity/api/v2/",
    (route) => {
      const search = new URL(route.request().url()).searchParams.get("search");
      const results = [percent, literal]
        .filter(({ query }) => query === search)
        .map(({ id, name }) => ({
          id,
          name,
          is_toplevel: true,
          permission: 8,
        }));
      return route.fulfill({ json: { count: results.length, results } });
    },
  );
  const failures = collectBrowserFailures(page);
  await page.goto(pastedUrl);
  await expectFilteredList(page, percent);

  await searchBox(page).fill(literal.query);
  await searchBox(page).press("Enter");
  await expectFilteredList(page, literal);
  const generatedUrl = new URL(page.url());
  expect(generatedUrl.searchParams.get("query")).toBe(literal.query);

  const tab = await context.newPage();
  const tabFailures = collectBrowserFailures(tab);
  await tab.goto(generatedUrl.href);
  await expectFilteredList(tab, literal);
  expectNoBrowserFailures(tabFailures);
  await tab.close();

  await page.goBack();
  await expect(page).toHaveURL(pastedUrl);
  await expectFilteredList(page, percent);
  await page.goForward();
  await expect(page).toHaveURL(generatedUrl.href);
  await expectFilteredList(page, literal);
  expectNoBrowserFailures(failures);
});
