/**
 * @jest-environment jsdom
 */

import {
  act,
  render,
  screen,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { TestWrapperWithoutRoutes } from "TestWrapper";
import { EntryReferral } from "components/entry/EntryReferral";
import { aironeApiClient } from "repository/AironeApiClient";

// Mock API client
jest.mock("repository/AironeApiClient", () => ({
  aironeApiClient: {
    getEntryReferral: jest.fn(),
  },
}));

const mockGetEntryReferral = aironeApiClient.getEntryReferral as jest.Mock;

const createMockReferrals = (count: number) => ({
  results: Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: `Entry ${i + 1}`,
    schema: {
      id: 100 + i,
      name: `Entity ${i + 1}`,
    },
  })),
  count,
});

describe("EntryReferral", () => {
  const renderComponent = async (entryId: number = 1) => {
    const router = createMemoryRouter([
      {
        path: "/",
        element: <EntryReferral entryId={entryId} />,
      },
    ]);

    await act(async () => {
      render(<RouterProvider router={router} />, {
        wrapper: TestWrapperWithoutRoutes,
      });
    });

    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockGetEntryReferral.mockResolvedValue(createMockReferrals(3));
  });

  describe("rendering", () => {
    test("should render referral count", async () => {
      await renderComponent();

      expect(screen.getByText(/関連づけられたアイテム.*3/)).toBeInTheDocument();
    });

    test("should render referral entries", async () => {
      await renderComponent();

      expect(screen.getByText("Entry 1")).toBeInTheDocument();
      expect(screen.getByText("Entry 2")).toBeInTheDocument();
      expect(screen.getByText("Entry 3")).toBeInTheDocument();
    });

    test("should render search box with placeholder", async () => {
      await renderComponent();

      expect(
        screen.getByPlaceholderText("アイテムを絞り込む"),
      ).toBeInTheDocument();
    });

    test("should render pagination", async () => {
      await renderComponent();

      expect(screen.getByRole("navigation")).toBeInTheDocument();
    });
  });

  describe("referral entry links", () => {
    test("should render referral entries as links", async () => {
      await renderComponent();

      const entryLink = screen.getByText("Entry 1").closest("a");
      expect(entryLink).toHaveAttribute("href");
      expect(entryLink?.getAttribute("href")).toContain("/entries/1");
    });

    test("should include entity id in link path", async () => {
      await renderComponent();

      const entryLink = screen.getByText("Entry 1").closest("a");
      // The link should be to the entry details page with entity/entry IDs
      expect(entryLink?.getAttribute("href")).toMatch(
        /\/entities\/\d+\/entries\/\d+/,
      );
    });
  });

  describe("empty state", () => {
    test("should render zero count when no referrals", async () => {
      mockGetEntryReferral.mockResolvedValue({
        results: [],
        count: 0,
      });

      await renderComponent();

      expect(screen.getByText(/関連づけられたアイテム.*0/)).toBeInTheDocument();
    });

    test("should not render entry items when no referrals", async () => {
      mockGetEntryReferral.mockResolvedValue({
        results: [],
        count: 0,
      });

      await renderComponent();

      expect(screen.queryByText("Entry 1")).not.toBeInTheDocument();
    });
  });

  describe("API calls", () => {
    test("should call getEntryReferral with correct entry ID", async () => {
      await renderComponent(42);

      expect(mockGetEntryReferral).toHaveBeenCalledWith(42, 1, undefined);
    });

    test("should fetch referrals on mount", async () => {
      await renderComponent();

      expect(mockGetEntryReferral).toHaveBeenCalled();
    });
  });

  describe("search functionality", () => {
    test("search box should be present and interactive", async () => {
      await renderComponent();

      const searchInput = screen.getByPlaceholderText("アイテムを絞り込む");
      expect(searchInput).toBeInTheDocument();

      // Should allow typing
      fireEvent.change(searchInput, { target: { value: "TestKeyword" } });
      expect(searchInput).toHaveValue("TestKeyword");
    });
  });

  describe("list structure", () => {
    test("should render referrals in a list with correct id", async () => {
      await renderComponent();

      // The referral list has id="ref_list"
      const refList = document.getElementById("ref_list");
      expect(refList).toBeInTheDocument();
      expect(refList?.tagName.toLowerCase()).toBe("ul");
    });

    test("should render list items for each referral in the referral list", async () => {
      await renderComponent();

      // Get only the list items within the referral list (not pagination)
      const refList = document.getElementById("ref_list");
      const listItems = refList?.querySelectorAll("li");
      expect(listItems).toHaveLength(3);
    });
  });

  describe("multiple entries", () => {
    test("should handle large number of referrals", async () => {
      mockGetEntryReferral.mockResolvedValue(createMockReferrals(10));

      await renderComponent();

      expect(
        screen.getByText(/関連づけられたアイテム.*10/),
      ).toBeInTheDocument();
    });
  });
});
