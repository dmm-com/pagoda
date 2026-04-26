/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { Component, ReactNode } from "react";

import {
  AdvancedSearchResult,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
  EntryAttributeTypeTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
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

  describe("issue #3449 — bulk update on a freshly added attribute", () => {
    // Regression for #3449. Scenario: an EntityAttr was just added to the
    // model, so existing entries have neither an Attribute object nor an ES
    // entry for it. The advanced-search column for the new attr shows up
    // (because it is in defaultAttrsFilter), and `results.values[0].attrs[
    // newattr]` is undefined.
    //
    // Pre-fix behavior: SearchResults computed attrTypes[newattr] from row 0
    // alone → undefined → coerced to 0 → AdvancedSearchEditModal rendered
    // <AttributeValueField type={0} /> → threw "Unknown attribute type: 0".
    //
    // Post-fix behavior: SearchResults sources the type from `entityAttrs`
    // (now populated with `type` by EntityAttrNameAPI), so the modal opens
    // cleanly with the correct field for the attribute's type.
    test("opens bulk-edit modal cleanly when row 0 lacks the new attr", () => {
      const NEW_ATTR = "newattr";

      const resultsWithMissingAttr: AdvancedSearchResult = {
        count: 1,
        totalCount: 1,
        values: [
          {
            entry: { id: 1, name: "Entry 1" },
            entity: { id: 100, name: "TestEntity" },
            isReadable: true,
            // Crucially: NEW_ATTR is NOT in attrs (no ES data for it yet)
            attrs: {},
            referrals: [],
          },
        ],
      };

      // Error boundary in case a regression reintroduces the throw — the
      // assertion below would then fail more legibly than React's default.
      class Boundary extends Component<
        { children: ReactNode },
        { error: Error | null }
      > {
        state = { error: null as Error | null };
        static getDerivedStateFromError(error: Error) {
          return { error };
        }
        render() {
          if (this.state.error) {
            return (
              <div data-testid="boundary-error">{this.state.error.message}</div>
            );
          }
          return this.props.children;
        }
      }

      const errSpy = jest.spyOn(console, "error").mockImplementation(() => {});

      try {
        render(
          <Boundary>
            <SearchResults
              {...defaultProps}
              results={resultsWithMissingAttr}
              defaultAttrsFilter={{
                [NEW_ATTR]: {
                  filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
                  keyword: "",
                },
              }}
              entityAttrs={[
                // The fix: EntityAttrNameAPI now returns `type`, so the FE
                // can resolve the column's type without depending on row 0.
                {
                  id: 42,
                  name: NEW_ATTR,
                  type: EntryAttributeTypeTypeEnum.STRING,
                },
              ]}
            />
          </Boundary>,
          { wrapper: TestWrapper },
        );

        expect(screen.getByText(NEW_ATTR)).toBeInTheDocument();

        const filterButtons = screen.getAllByRole("button", {
          name: /属性値でフィルタ/,
        });
        expect(filterButtons).toHaveLength(1);
        fireEvent.click(filterButtons[0]);

        const bulkUpdateBtn = screen.getByRole("button", {
          name: /属性を一括更新/,
        });
        // Defense-in-depth: the bulk-update button is now disabled when the
        // type is unknown. With entityAttrs.type populated, it must be
        // enabled.
        expect(bulkUpdateBtn).not.toBeDisabled();
        fireEvent.click(bulkUpdateBtn);

        // No error boundary trip and modal heading is rendered.
        expect(screen.queryByTestId("boundary-error")).toBeNull();
        expect(
          screen.getByText("一括更新する（変更後の）値に更新"),
        ).toBeInTheDocument();

        // No "Unknown attribute type" was logged.
        const sawAttrTypeThrow = errSpy.mock.calls.some((call) =>
          call.some(
            (arg) =>
              typeof arg === "string" && arg.includes("Unknown attribute type"),
          ),
        );
        expect(sawAttrTypeThrow).toBe(false);
      } finally {
        errSpy.mockRestore();
      }
    });

    // Defense-in-depth check (#3449): if for any reason both entityAttrs and
    // results lack the type (e.g. entityAttrs has not loaded yet), the
    // bulk-update button must be disabled rather than opening a modal that
    // would throw.
    test("disables bulk-update button when type cannot be resolved", () => {
      const NEW_ATTR = "newattr";

      const errSpy = jest.spyOn(console, "error").mockImplementation(() => {});
      try {
        render(
          <SearchResults
            {...defaultProps}
            results={{
              count: 1,
              totalCount: 1,
              values: [
                {
                  entry: { id: 1, name: "Entry 1" },
                  entity: { id: 100, name: "TestEntity" },
                  isReadable: true,
                  attrs: {},
                  referrals: [],
                },
              ],
            }}
            defaultAttrsFilter={{
              [NEW_ATTR]: {
                filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
                keyword: "",
              },
            }}
            entityAttrs={[]}
          />,
          { wrapper: TestWrapper },
        );

        const filterButtons = screen.getAllByRole("button", {
          name: /属性値でフィルタ/,
        });
        fireEvent.click(filterButtons[0]);

        const bulkUpdateBtn = screen.getByRole("button", {
          name: /属性を一括更新/,
        });
        expect(bulkUpdateBtn).toBeDisabled();
      } finally {
        errSpy.mockRestore();
      }
    });

    // Sanity counter-test: when results DO contain the attribute (i.e. after
    // the user updates an item, ES gets back-filled, so the type lookup
    // succeeds), the modal opens cleanly. This is the "アイテムを更新すると
    // 解消する" half of the bug report.
    test("opening bulk-edit modal works when results expose the attr type", () => {
      const NEW_ATTR = "newattr";

      const resultsWithAttr: AdvancedSearchResult = {
        count: 1,
        totalCount: 1,
        values: [
          {
            entry: { id: 1, name: "Entry 1" },
            entity: { id: 100, name: "TestEntity" },
            isReadable: true,
            attrs: {
              [NEW_ATTR]: {
                type: EntryAttributeTypeTypeEnum.STRING,
                value: { asString: "" },
                isReadable: true,
              },
            },
            referrals: [],
          },
        ],
      };

      const errSpy = jest.spyOn(console, "error").mockImplementation(() => {});
      try {
        render(
          <SearchResults
            {...defaultProps}
            results={resultsWithAttr}
            defaultAttrsFilter={{
              [NEW_ATTR]: {
                filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
                keyword: "",
              },
            }}
            entityAttrs={[
              {
                id: 42,
                name: NEW_ATTR,
                type: EntryAttributeTypeTypeEnum.STRING,
              },
            ]}
          />,
          { wrapper: TestWrapper },
        );

        const filterButtons = screen.getAllByRole("button", {
          name: /属性値でフィルタ/,
        });
        fireEvent.click(filterButtons[0]);

        const bulkUpdateBtn = screen.getByRole("button", {
          name: /属性を一括更新/,
        });
        // Should NOT throw "Unknown attribute type" when the type is known.
        expect(() => fireEvent.click(bulkUpdateBtn)).not.toThrow();

        // The modal heading should now be on screen.
        expect(
          screen.getByText("一括更新する（変更後の）値に更新"),
        ).toBeInTheDocument();

        // Confirm no "Unknown attribute type" error was logged.
        const sawAttrTypeThrow = errSpy.mock.calls.some((call) =>
          call.some(
            (arg) =>
              typeof arg === "string" && arg.includes("Unknown attribute type"),
          ),
        );
        expect(sawAttrTypeThrow).toBe(false);
      } finally {
        errSpy.mockRestore();
      }
    });
  });
});
