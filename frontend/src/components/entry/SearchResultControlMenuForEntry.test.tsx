/**
 */

import {
  EntryHint,
  EntryHintFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { act, render, screen } from "@testing-library/react";

import { SearchResultControlMenuForEntry } from "./SearchResultControlMenuForEntry";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

describe("SearchResultControlMenuForEntry", () => {
  const defaultProps = {
    hintEntry: {
      filterKey: EntryHintFilterKeyEnum.CLEARED,
      keyword: "",
    } as EntryHint,
    anchorElem: null,
    handleClose: vi.fn(),
    hintEntryDispatcher: vi.fn(),
    handleSelectFilterConditions: vi.fn(),
    setOpenEditModal: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
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

  test("renders in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });
    const anchorElem = document.createElement("button");
    render(
      <SearchResultControlMenuForEntry
        {...defaultProps}
        anchorElem={anchorElem}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByText("Filter conditions")).toBeInTheDocument();
    expect(screen.getByText("Clear")).toBeInTheDocument();
  });
});
