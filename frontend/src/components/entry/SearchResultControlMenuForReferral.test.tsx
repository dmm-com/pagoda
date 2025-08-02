/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";

import { SearchResultControlMenuForReferral } from "./SearchResultControlMenuForReferral";

import { TestWrapper } from "TestWrapper";

// Mock the location object
const mockLocation = {
  search: "",
};
Object.defineProperty(window, "location", {
  value: mockLocation,
  writable: true,
});

describe("SearchResultControlMenuForReferral", () => {
  const defaultProps = {
    referralFilter: "",
    anchorElem: null,
    handleClose: jest.fn(),
    referralFilterDispatcher: jest.fn(),
    handleSelectFilterConditions: jest.fn(),
    handleClear: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockLocation.search = "";
  });

  test("should render menu when anchorElem is provided", () => {
    const anchorElem = document.createElement("button");
    const { container } = render(
      <SearchResultControlMenuForReferral
        {...defaultProps}
        anchorElem={anchorElem}
      />,
      { wrapper: TestWrapper },
    );

    expect(container).toBeInTheDocument();
  });

  test("should not render menu when anchorElem is null", () => {
    const { container } = render(
      <SearchResultControlMenuForReferral
        {...defaultProps}
        anchorElem={null}
      />,
      { wrapper: TestWrapper },
    );

    expect(container).toBeInTheDocument();
  });
});
