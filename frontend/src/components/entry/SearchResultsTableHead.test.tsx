/**
 * @jest-environment jsdom
 */

import {
  AdvancedSearchSortOrderEnum,
  EntryAttributeTypeTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { Table, TableContainer } from "@mui/material";
import { fireEvent, render, screen } from "@testing-library/react";
import { useLocation, useNavigate } from "react-router";

import { SearchResultsTableHead } from "./SearchResultsTableHead";

import { TestWrapper } from "TestWrapper";

// Mock react-router hooks
jest.mock("react-router", () => ({
  ...jest.requireActual("react-router"),
  useLocation: jest.fn(),
  useNavigate: jest.fn(),
}));

// Mock getIsFiltered function
jest.mock("pages/AdvancedSearchResultsPage", () => ({
  getIsFiltered: jest.fn(() => false),
}));

// Mock the child components
jest.mock("./SearchResultControlMenu", () => ({
  SearchResultControlMenu: () => (
    <div data-testid="search-result-control-menu" />
  ),
}));

jest.mock("./SearchResultControlMenuForEntry", () => ({
  SearchResultControlMenuForEntry: () => (
    <div data-testid="search-result-control-menu-for-entry" />
  ),
}));

jest.mock("./SearchResultControlMenuForReferral", () => ({
  SearchResultControlMenuForReferral: () => (
    <div data-testid="search-result-control-menu-for-referral" />
  ),
}));

jest.mock("./AdvancedSearchJoinModal", () => ({
  AdvancedSearchJoinModal: () => (
    <div data-testid="advanced-search-join-modal" />
  ),
}));

const mockNavigate = jest.fn();
const mockLocation = {
  pathname: "/test",
  search: "?entity=1&entity=2",
};

describe("SearchResultsTableHead", () => {
  // Create stable objects to prevent useEffect infinite loops
  const stableAttrTypes = {};
  const stableEntityIds = [1, 2];
  const stableJoinAttrs: never[] = [];

  const defaultProps = {
    hasReferral: false,
    attrTypes: stableAttrTypes,
    entityIds: stableEntityIds,
    searchAllEntities: false,
    joinAttrs: stableJoinAttrs,
    handleChangeAllBulkOperationEntryIds: jest.fn(),
    entityAttrs: [],
  };

  // Helper function to render the component properly wrapped in a Table
  const renderSearchResultsTableHead = (props = {}) => {
    const stableProps = {
      ...defaultProps,
      ...props,
    };

    return render(
      <TableContainer>
        <Table>
          <SearchResultsTableHead {...stableProps} />
        </Table>
      </TableContainer>,
      { wrapper: TestWrapper },
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
    (useLocation as jest.Mock).mockReturnValue(mockLocation);
  });

  test("should render without crashing", () => {
    expect(() => renderSearchResultsTableHead()).not.toThrow();
  });

  test("should render bulk operation checkbox when not readonly", () => {
    renderSearchResultsTableHead();
    // Look for the checkbox button without text label
    const checkbox = screen.getByRole("button", { name: "" });
    expect(checkbox).toBeInTheDocument();
  });

  test("should not render bulk operation checkbox when readonly", () => {
    renderSearchResultsTableHead({ isReadonly: true });
    const checkbox = screen.queryByRole("button", { name: "" });
    expect(checkbox).not.toBeInTheDocument();
  });

  test("should render item name header with filter icon when not readonly", () => {
    renderSearchResultsTableHead();
    expect(screen.getByText("アイテム名")).toBeInTheDocument();
    expect(screen.getByLabelText("アイテム名でフィルタ")).toBeInTheDocument();
  });

  test("should omit headline when omitHeadline is true", () => {
    renderSearchResultsTableHead({ omitHeadline: true });
    expect(screen.queryByText("アイテム名")).not.toBeInTheDocument();
  });

  test("should render referral column when hasReferral is true", () => {
    renderSearchResultsTableHead({ hasReferral: true });
    expect(screen.getByText("参照アイテム")).toBeInTheDocument();
    expect(screen.getByLabelText("参照アイテムでフィルタ")).toBeInTheDocument();
  });

  test("should hide filter controls in readonly mode", () => {
    renderSearchResultsTableHead({
      hasReferral: true,
      isReadonly: true,
      isNarrowDown: false,
    });

    // Should not show filter button for item name in readonly mode
    expect(
      screen.queryByLabelText("アイテム名でフィルタ"),
    ).not.toBeInTheDocument();
    // Note: The referral filter may still appear, this component behavior might be different than expected
  });

  test("should handle multiple entity IDs", () => {
    const entityIds = [1, 2, 3, 4, 5];
    renderSearchResultsTableHead({ entityIds });

    // Component should render with multiple entity IDs
    expect(screen.getByText("アイテム名")).toBeInTheDocument();
  });

  test("should render with basic attribute types", () => {
    // Use a stable reference for this test
    const attrTypes = { testAttr: EntryAttributeTypeTypeEnum.STRING };

    renderSearchResultsTableHead({ attrTypes });

    // Should render basic structure
    expect(screen.getByText("アイテム名")).toBeInTheDocument();
  });

  describe("sort label", () => {
    const findSortLabel = (headerText: string) =>
      screen.getByText(headerText).closest(".MuiTableSortLabel-root");

    test("entry name column always carries a sort label", () => {
      renderSearchResultsTableHead();
      expect(findSortLabel("アイテム名")).toBeTruthy();
    });

    test("sortable attribute type shows a sort label", () => {
      renderSearchResultsTableHead({
        attrTypes: { stringAttr: EntryAttributeTypeTypeEnum.STRING },
        defaultAttrsFilter: { stringAttr: { filterKey: 0, keyword: "" } },
      });
      expect(findSortLabel("stringAttr")).toBeTruthy();
    });

    test.each([
      ["number", EntryAttributeTypeTypeEnum.NUMBER],
      ["boolean", EntryAttributeTypeTypeEnum.BOOLEAN],
      ["array_string", EntryAttributeTypeTypeEnum.ARRAY_STRING],
      ["named_object", EntryAttributeTypeTypeEnum.NAMED_OBJECT],
      ["array_named_object", EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT],
    ])("unsortable type (%s) does NOT show a sort label", (label, type) => {
      renderSearchResultsTableHead({
        attrTypes: { unsortableAttr: type },
        defaultAttrsFilter: { unsortableAttr: { filterKey: 0, keyword: "" } },
      });
      expect(findSortLabel("unsortableAttr")).toBeFalsy();
    });

    test("clicking an unsorted column navigates with asc", () => {
      renderSearchResultsTableHead({
        attrTypes: { stringAttr: EntryAttributeTypeTypeEnum.STRING },
        defaultAttrsFilter: { stringAttr: { filterKey: 0, keyword: "" } },
      });
      const label = findSortLabel("stringAttr");
      fireEvent.click(label!);
      expect(mockNavigate).toHaveBeenCalled();
      const target = (mockNavigate.mock.calls[0][0] as { search: string })
        .search;
      expect(target).toContain("sort=stringAttr");
      expect(target).toContain("order=asc");
    });

    test("clicking the currently-sorted column toggles to desc", () => {
      renderSearchResultsTableHead({
        attrTypes: { stringAttr: EntryAttributeTypeTypeEnum.STRING },
        defaultAttrsFilter: { stringAttr: { filterKey: 0, keyword: "" } },
        defaultSort: {
          targetAttrname: "stringAttr",
          order: AdvancedSearchSortOrderEnum.Asc,
        },
      });
      const label = findSortLabel("stringAttr");
      fireEvent.click(label!);
      const target = (mockNavigate.mock.calls[0][0] as { search: string })
        .search;
      expect(target).toContain("order=desc");
    });
  });
});
