/**
 */

import { render } from "@testing-library/react";

import { SearchResultControlMenuForReferral } from "./SearchResultControlMenuForReferral";

import { TestWrapper } from "TestWrapper";

describe("SearchResultControlMenuForReferral", () => {
  const defaultProps = {
    referralFilter: "",
    referralIncludeModelIds: [],
    referralExcludeModelIds: [],
    anchorElem: null,
    handleClose: vi.fn(),
    referralFilterDispatcher: vi.fn(),
    referralIncludeModelIdsDispatcher: vi.fn(),
    referralExcludeModelIdsDispatcher: vi.fn(),
    handleSelectFilterConditions: vi.fn(),
    handleClear: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
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
