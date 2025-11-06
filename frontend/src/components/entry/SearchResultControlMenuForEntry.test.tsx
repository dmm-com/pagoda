/**
 * @jest-environment jsdom
 */

import {
  EntryHint,
  EntryHintFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen } from "@testing-library/react";

import { SearchResultControlMenuForEntry } from "./SearchResultControlMenuForEntry";

import { TestWrapper } from "TestWrapper";

describe("SearchResultControlMenuForEntry", () => {
  const defaultProps = {
    hintEntry: {
      filterKey: EntryHintFilterKeyEnum.CLEARED,
      keyword: "",
    } as EntryHint,
    anchorElem: null,
    handleClose: jest.fn(),
    hintEntryDispatcher: jest.fn(),
    handleSelectFilterConditions: jest.fn(),
    setOpenEditModal: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("should render menu when anchorElem is provided", () => {
    const anchorElem = document.createElement("button");
    render(
      <SearchResultControlMenuForEntry
        {...defaultProps}
        anchorElem={anchorElem}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByText("絞り込み条件")).toBeInTheDocument();
    expect(screen.getByText("クリア")).toBeInTheDocument();
  });

  test("should not render menu when anchorElem is null", () => {
    const { container } = render(
      <SearchResultControlMenuForEntry {...defaultProps} anchorElem={null} />,
      { wrapper: TestWrapper },
    );

    expect(container.querySelectorAll('[role="menuitem"]')).toHaveLength(0);
  });
});
