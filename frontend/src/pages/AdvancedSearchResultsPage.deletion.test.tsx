import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { TestWrapper } from "TestWrapper";
import { AdvancedSearchResultsPage } from "pages/AdvancedSearchResultsPage";
import { aironeApiClient } from "repository/AironeApiClient";

vi.mock("repository/AironeApiClient", () => ({
  aironeApiClient: {
    getEntityAttrs: vi.fn(),
    advancedSearch: vi.fn(),
    getEntry: vi.fn(),
    getEntryReferral: vi.fn(),
    destroyEntries: vi.fn(),
  },
}));

vi.mock("components/entry/SearchResults", () => ({
  SearchResults: ({
    setBulkOperationEntryIds,
  }: {
    setBulkOperationEntryIds: (ids: number[]) => void;
  }) => (
    <button
      onClick={() =>
        setBulkOperationEntryIds(Array.from({ length: 100 }, (_, i) => i + 1))
      }
    >
      select targets
    </button>
  ),
}));

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(aironeApiClient.getEntityAttrs).mockResolvedValue([]);
  vi.mocked(aironeApiClient.advancedSearch).mockResolvedValue({
    count: 0,
    totalCount: 0,
    values: [],
  });
  vi.mocked(aironeApiClient.getEntry).mockImplementation(
    async (id) =>
      ({ id, schema: { id: 1 } }) as Awaited<
        ReturnType<typeof aironeApiClient.getEntry>
      >,
  );
  vi.mocked(aironeApiClient.getEntryReferral).mockResolvedValue({
    count: 0,
    results: [],
  });
  vi.mocked(aironeApiClient.destroyEntries).mockResolvedValue();
});

test("checks items outside the visible page before deleting all matches", async () => {
  render(<AdvancedSearchResultsPage />, { wrapper: TestWrapper });
  fireEvent.click(await screen.findByText("select targets"));
  fireEvent.click(await screen.findByRole("checkbox"));
  vi.mocked(aironeApiClient.advancedSearch).mockResolvedValue({
    count: 1,
    totalCount: 1,
    values: [{ entry: { id: 101 }, entity: { id: 1 } }],
  } as Awaited<ReturnType<typeof aironeApiClient.advancedSearch>>);
  vi.mocked(aironeApiClient.getEntryReferral).mockImplementation(
    async (id) =>
      ({
        count: id === 101 ? 1 : 0,
        results:
          id === 101
            ? [
                {
                  id: 999,
                  name: "dependent-item",
                  schema: { id: 10, name: "OtherModel" },
                },
              ]
            : [],
      }) as Awaited<ReturnType<typeof aironeApiClient.getEntryReferral>>,
  );
  fireEvent.click(screen.getByRole("button", { name: "まとめて削除" }));
  await screen.findByRole("link", { name: "OtherModel / dependent-item" });
  expect(aironeApiClient.getEntryReferral).toHaveBeenCalledWith(101, 1);
  expect(
    screen.queryByRole("button", { name: /yes/i }),
  ).not.toBeInTheDocument();
  expect(aironeApiClient.destroyEntries).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "影響を理解して削除" }));
  await waitFor(() =>
    expect(aironeApiClient.destroyEntries).toHaveBeenCalledWith(
      Array.from({ length: 100 }, (_, i) => i + 1),
      "[]",
      true,
    ),
  );
});

test("cancelling the reference warning prevents the entire bulk deletion", async () => {
  vi.mocked(aironeApiClient.getEntryReferral).mockResolvedValue({
    count: 1,
    results: [
      {
        id: 999,
        name: "dependent-item",
        schema: { id: 10, name: "OtherModel" },
      },
    ],
  } as Awaited<ReturnType<typeof aironeApiClient.getEntryReferral>>);
  render(<AdvancedSearchResultsPage />, { wrapper: TestWrapper });
  fireEvent.click(await screen.findByText("select targets"));
  fireEvent.click(screen.getByRole("button", { name: "まとめて削除" }));
  await screen.findAllByRole("link", { name: "OtherModel / dependent-item" });
  fireEvent.click(screen.getByRole("button", { name: "キャンセル" }));
  await waitFor(() =>
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
  );
  expect(
    screen.queryByRole("button", { name: /yes/i }),
  ).not.toBeInTheDocument();
  expect(aironeApiClient.destroyEntries).not.toHaveBeenCalled();
});
