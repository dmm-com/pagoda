/**
 * @jest-environment jsdom
 */

import { AdvancedSearchResultAttrInfoFilterKeyEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen } from "@testing-library/react";
import React from "react";

import { SearchResultControlMenu } from "./SearchResultControlMenu";

import { TestWrapper } from "TestWrapper";

describe("SearchResultControlMenu", () => {
  const defaultProps = {
    attrFilter: {
      filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
      keyword: "",
    },
    anchorElem: null,
    handleUpdateAttrFilter: jest.fn(),
    handleSelectFilterConditions: jest.fn(),
    handleClose: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("should render menu when anchorElem is provided", () => {
    const anchorElem = document.createElement("button");
    render(
      <SearchResultControlMenu {...defaultProps} anchorElem={anchorElem} />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByText("絞り込み条件")).toBeInTheDocument();
  });

  test("should not render menu when anchorElem is null", () => {
    const { container } = render(
      <SearchResultControlMenu {...defaultProps} anchorElem={null} />,
      { wrapper: TestWrapper },
    );

    expect(container.querySelectorAll('[role="menuitem"]')).toHaveLength(0);
  });
});
