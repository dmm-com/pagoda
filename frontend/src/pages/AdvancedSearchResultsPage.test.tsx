/**
 */

import {
  render,
  screen,
  act,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { MemoryRouter } from "react-router";

import { TestWrapper, TestWrapperWithoutRoutes } from "TestWrapper";
import i18n from "i18n/config";
import {
  AdvancedSearchResultsPage,
  getDisplayedSearchResultCount,
} from "pages/AdvancedSearchResultsPage";

const server = setupServer(
  // getEntityAttrs
  http.get(
    "http://localhost/entity/api/v2/attrs?entity_ids=1&referral_attr=",
    () => {
      return HttpResponse.json([]);
    },
  ),
  // advancedSearch
  http.post("http://localhost/entry/api/v2/advanced_search/", () => {
    return HttpResponse.json({
      count: 1,
      total_count: 1,
      values: [
        {
          entry: {
            id: 2,
            name: "entry1",
          },
          entity: {
            id: 1,
            name: "entity1",
          },
          attrs: {
            attr1: {
              type: 2,
              value: { asString: "attr1" },
              isReadable: true,
            },
            attr2: {
              type: 2,
              value: { asString: "attr1" },
              isReadable: true,
            },
          },
          isReadable: true,
        },
      ],
    });
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test("should call advanced search once when changing to the next page", async () => {
  const requests: Array<Record<string, unknown>> = [];
  server.use(
    http.post(
      "http://localhost/entry/api/v2/advanced_search/",
      async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        requests.push(body);
        return HttpResponse.json({ count: 1, total_count: 101, values: [] });
      },
    ),
  );

  await act(async () => {
    render(<AdvancedSearchResultsPage />, { wrapper: TestWrapper });
  });
  await waitFor(() =>
    expect(screen.queryByTestId("loading")).not.toBeInTheDocument(),
  );
  fireEvent.click(screen.getByLabelText("Go to page 2"));

  await waitFor(() => expect(requests).toHaveLength(2));
  expect(requests[0].entry_offset).toBe(0);
  expect(requests[1].entry_offset).toBe(100);
});

test("starts with no checked items and preserves explicit selections across pages", async () => {
  server.use(
    http.post(
      "http://localhost/entry/api/v2/advanced_search/",
      async ({ request }) => {
        const body = (await request.json()) as { entry_offset?: number };
        const secondPage = body.entry_offset === 100;
        return HttpResponse.json({
          count: 1,
          total_count: 101,
          values: [
            {
              entry: {
                id: secondPage ? 3 : 2,
                name: secondPage ? "entry2" : "entry1",
              },
              entity: { id: 1, name: "entity1" },
              attrs: {},
              is_readable: true,
            },
          ],
        });
      },
    ),
  );

  render(<AdvancedSearchResultsPage />, { wrapper: TestWrapper });
  const first = await screen.findByRole("checkbox");
  expect(first).not.toBeChecked();
  fireEvent.click(first);
  expect(first).toBeChecked();

  fireEvent.click(screen.getByLabelText("Go to page 2"));
  await screen.findByText("entry2");
  expect(screen.getByRole("checkbox")).not.toBeChecked();

  fireEvent.click(screen.getByLabelText("Go to page 1"));
  await screen.findByText("entry1");
  expect(screen.getByRole("checkbox")).toBeChecked();
});

test("should cap the displayed loaded count at the total count", () => {
  expect(getDisplayedSearchResultCount(2, 160, 100)).toBe(160);
  expect(getDisplayedSearchResultCount(2, 200, 100)).toBe(200);
  expect(getDisplayedSearchResultCount(1, 160, 100)).toBe(100);
});

test("should match snapshot", async () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        id: 1,
        username: "user1",
        isSuperuser: false,
        isReadonly: false,
        parentUser: null,
        email: "user1@example.com",
      },
    },
    writable: false,
  });

  // wait async calls and get rendered fragment
  const result = await act(async () => {
    return render(<AdvancedSearchResultsPage />, {
      wrapper: TestWrapper,
    });
  });
  await waitFor(() => {
    expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
  });

  expect(result).toMatchSnapshot();
});

test.each([
  true,
  false,
])("exports CSV with the selected split setting (%s)", async (splitArrayValues) => {
  const requests: unknown[] = [];
  server.use(
    http.post(
      "http://localhost/entry/api/v2/advanced_search_result_export/",
      async ({ request }) => {
        requests.push(await request.json());
        return new HttpResponse(null, { status: 200 });
      },
    ),
  );

  const search = new URLSearchParams({
    join_attrs: JSON.stringify({
      name: "IP Addresses",
      attrinfo: [{ name: "Network", keyword: "164" }],
    }),
  });
  render(
    <MemoryRouter initialEntries={[`/?${search}`]}>
      <AdvancedSearchResultsPage />
    </MemoryRouter>,
    { wrapper: TestWrapperWithoutRoutes },
  );
  const exportLabel = i18n.t("advancedSearch.resultsPage.exportCsv");
  const exportButton = screen.getByRole("button", { name: exportLabel });
  fireEvent.click(exportButton);
  const dialog = within(screen.getByRole("dialog"));
  expect(requests).toHaveLength(0);
  expect(
    dialog.getByRole("radio", {
      name: i18n.t("advancedSearch.resultsPage.csvLayoutSplit"),
    }),
  ).toBeChecked();

  fireEvent.click(
    dialog.getByRole("button", { name: i18n.t("common.cancel") }),
  );
  await waitFor(() =>
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
  );
  expect(requests).toHaveLength(0);

  fireEvent.click(exportButton);
  const reopenedDialog = within(screen.getByRole("dialog"));
  if (!splitArrayValues) {
    fireEvent.click(
      reopenedDialog.getByRole("radio", {
        name: i18n.t("advancedSearch.resultsPage.csvLayoutGrouped"),
      }),
    );
  }
  fireEvent.click(reopenedDialog.getByRole("button", { name: exportLabel }));

  await waitFor(() =>
    expect(requests).toEqual([
      expect.objectContaining({
        export_style: "csv",
        split_array_values: splitArrayValues,
        join_attrs: [
          expect.objectContaining({
            name: "IP Addresses",
            attrinfo: [
              expect.objectContaining({ name: "Network", keyword: "164" }),
            ],
          }),
        ],
      }),
    ]),
  );
});

test("renders in English", async () => {
  // "should match snapshot" (which runs before this test in this file)
  // already defines window.django_context as a non-writable property.
  await act(async () => {
    await i18n.changeLanguage("en");
  });

  await act(async () => {
    render(<AdvancedSearchResultsPage />, {
      wrapper: TestWrapper,
    });
  });
  await waitFor(() => {
    expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
  });

  expect(screen.getAllByText("Search results").length).toBeGreaterThan(0);
  expect(screen.getAllByText("Advanced Search").length).toBeGreaterThan(0);
  expect(screen.getByText("Reset attributes")).toBeInTheDocument();
  expect(screen.getByText("Export YAML")).toBeInTheDocument();
  expect(screen.getByText("Export CSV")).toBeInTheDocument();
  expect(screen.getByText("Bulk delete")).toBeInTheDocument();
});
