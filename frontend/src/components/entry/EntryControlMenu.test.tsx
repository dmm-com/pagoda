/**
 * @jest-environment jsdom
 */

import { render, screen } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { EntryControlMenu } from "components/entry/EntryControlMenu";

describe("EntryControlMenu", () => {
  test("should render a component with essential props", function () {
    const anchorElem = document.createElement("button");
    const handleClose = () => undefined;

    expect(() =>
      render(
        <EntryControlMenu
          entityId={0}
          entryId={0}
          anchorElem={anchorElem}
          handleClose={handleClose}
        />,
        {
          wrapper: TestWrapper,
        },
      ),
    ).not.toThrow();
  });

  test("should render a component with optional props", function () {
    const anchorElem = document.createElement("button");
    const handleClose = () => undefined;

    expect(() =>
      render(
        <EntryControlMenu
          entityId={0}
          entryId={0}
          anchorElem={anchorElem}
          handleClose={handleClose}
          disableChangeHistory={true}
        />,
        {
          wrapper: TestWrapper,
        },
      ),
    ).not.toThrow();
  });

  test("menu items are displayed correctly", () => {
    // specify anchorElem to open the menu
    render(
      <EntryControlMenu
        entityId={1}
        entryId={1}
        anchorElem={document.createElement("button")}
        handleClose={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // menu items text should be displayed
    expect(screen.getByText("詳細")).toBeInTheDocument();
    expect(screen.getByText("編集")).toBeInTheDocument();
    expect(screen.getByText("コピー")).toBeInTheDocument();
    expect(screen.getByText("ACL 設定")).toBeInTheDocument();
    expect(screen.getByText("変更履歴")).toBeInTheDocument();
    expect(screen.getByText("ACL 変更履歴")).toBeInTheDocument();
    expect(screen.getByText("削除")).toBeInTheDocument();
  });

  test("anchorElem is null, menu is closed", () => {
    const { container } = render(
      <EntryControlMenu
        entityId={1}
        entryId={1}
        anchorElem={null}
        handleClose={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // menu should be closed, so menu items should not be displayed
    const menuItems = container.querySelectorAll(".MuiMenuItem-root");
    expect(menuItems.length).toBe(0);
  });

  test("disableChangeHistory prop works correctly", () => {
    // Render with disableChangeHistory=true
    const { rerender } = render(
      <EntryControlMenu
        entityId={1}
        entryId={1}
        anchorElem={document.createElement("button")}
        handleClose={() => {}}
        disableChangeHistory={true}
      />,
      { wrapper: TestWrapper },
    );

    // Check "変更履歴" menu item is displayed (disabled state)
    const historyText = screen.getByText("変更履歴");
    expect(historyText).toBeInTheDocument();

    // Render with disableChangeHistory=false
    rerender(
      <EntryControlMenu
        entityId={1}
        entryId={1}
        anchorElem={document.createElement("button")}
        handleClose={() => {}}
        disableChangeHistory={false}
      />,
    );

    // Check "変更履歴" menu item is displayed (enabled state)
    const enabledHistoryText = screen.getByText("変更履歴");
    expect(enabledHistoryText).toBeInTheDocument();
  });
});
