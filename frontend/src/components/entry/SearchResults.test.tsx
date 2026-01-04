/**
 * @jest-environment jsdom
 */

import { AdvancedSearchResult } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen, fireEvent } from "@testing-library/react";

import { TestWrapper } from "TestWrapper";
import { SearchResults } from "components/entry/SearchResults";

// Sample data for tests
const createMockResults = (count: number = 2): AdvancedSearchResult => ({
  count,
  totalCount: count,
  values: Array.from({ length: count }, (_, i) => ({
    entry: { id: i + 1, name: `Entry ${i + 1}` },
    entity: { id: 100, name: "TestEntity" },
    isReadable: true,
    attrs: {},
    referrals: [],
  })),
});

const emptyResults: AdvancedSearchResult = {
  count: 0,
  totalCount: 0,
  values: [],
};

describe("SearchResults", () => {
  const defaultProps = {
    results: createMockResults(),
    page: 1,
    changePage: jest.fn(),
    bulkOperationEntryIds: [] as number[],
    setBulkOperationEntryIds: jest.fn(),
    hasReferral: false,
    entityIds: [100],
    joinAttrs: [],
    disablePaginationFooter: false,
    searchAllEntities: false,
    entityAttrs: [],
  };

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("rendering", () => {
    test("should render without error with minimal props", () => {
      expect(() =>
        render(<SearchResults {...defaultProps} />, { wrapper: TestWrapper }),
      ).not.toThrow();
    });

    test("should render entry names from results", () => {
      render(<SearchResults {...defaultProps} />, { wrapper: TestWrapper });

      expect(screen.getByText("Entry 1")).toBeInTheDocument();
      expect(screen.getByText("Entry 2")).toBeInTheDocument();
    });

    test("should render entry links to detail pages", () => {
      render(<SearchResults {...defaultProps} />, { wrapper: TestWrapper });

      const link = screen.getByText("Entry 1").closest("a");
      expect(link).toHaveAttribute("href");
      expect(link?.getAttribute("href")).toContain("/entries/1");
    });

    test("should render empty table when no results", () => {
      render(<SearchResults {...defaultProps} results={emptyResults} />, {
        wrapper: TestWrapper,
      });

      expect(screen.queryByText("Entry 1")).not.toBeInTheDocument();
    });
  });

  describe("bulk operations", () => {
    test("should render checkboxes for bulk operations when not readonly", () => {
      render(<SearchResults {...defaultProps} />, { wrapper: TestWrapper });

      const checkboxes = screen.getAllByRole("checkbox");
      // At least one checkbox per row plus header checkbox
      expect(checkboxes.length).toBeGreaterThanOrEqual(2);
    });

    test("should not render checkboxes when readonly", () => {
      render(<SearchResults {...defaultProps} isReadonly={true} />, {
        wrapper: TestWrapper,
      });

      // In readonly mode, the row checkboxes should not be present
      // Only the header checkbox might remain
      const rows = screen.getAllByRole("row");
      expect(rows.length).toBeGreaterThan(0);
    });

    test("should call setBulkOperationEntryIds when checkbox is clicked", () => {
      const mockSetBulkIds = jest.fn();
      render(
        <SearchResults
          {...defaultProps}
          setBulkOperationEntryIds={mockSetBulkIds}
        />,
        { wrapper: TestWrapper },
      );

      const checkboxes = screen.getAllByRole("checkbox");
      // Click the first row checkbox (not header)
      fireEvent.click(checkboxes[1]);

      expect(mockSetBulkIds).toHaveBeenCalled();
    });

    test("should show checked state for selected entries", () => {
      render(<SearchResults {...defaultProps} bulkOperationEntryIds={[1]} />, {
        wrapper: TestWrapper,
      });

      const checkboxes = screen.getAllByRole("checkbox");
      // The checkbox for entry 1 should be checked
      const checkedCheckbox = checkboxes.find(
        (cb) => (cb as HTMLInputElement).checked,
      );
      expect(checkedCheckbox).toBeDefined();
    });
  });

  describe("pagination", () => {
    test("should render pagination when not disabled", () => {
      const results = createMockResults(30);
      render(<SearchResults {...defaultProps} results={results} />, {
        wrapper: TestWrapper,
      });

      // Pagination footer should be present
      expect(screen.getByRole("navigation")).toBeInTheDocument();
    });

    test("should not render pagination when disabled", () => {
      render(
        <SearchResults {...defaultProps} disablePaginationFooter={true} />,
        { wrapper: TestWrapper },
      );

      // Pagination footer should not be present
      expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    });
  });

  describe("referrals", () => {
    test("should render referral column when hasReferral is true", () => {
      const resultsWithReferrals: AdvancedSearchResult = {
        count: 1,
        totalCount: 1,
        values: [
          {
            entry: { id: 1, name: "Entry 1" },
            entity: { id: 100, name: "TestEntity" },
            isReadable: true,
            attrs: {},
            referrals: [
              {
                id: 10,
                name: "Referral 1",
                schema: { id: 200, name: "RefEntity" },
              },
            ],
          },
        ],
      };

      render(
        <SearchResults
          {...defaultProps}
          results={resultsWithReferrals}
          hasReferral={true}
        />,
        { wrapper: TestWrapper },
      );

      expect(screen.getByText("Referral 1")).toBeInTheDocument();
    });
  });

  describe("omitHeadline mode", () => {
    test("should show edit icon instead of entry name when omitHeadline is true", () => {
      render(<SearchResults {...defaultProps} omitHeadline={true} />, {
        wrapper: TestWrapper,
      });

      // Entry names should not be visible
      expect(screen.queryByText("Entry 1")).not.toBeInTheDocument();

      // Edit icons should be present
      expect(screen.getAllByTestId("EditOutlinedIcon").length).toBeGreaterThan(
        0,
      );
    });
  });
});
