/**
 * @jest-environment jsdom
 */

import { render, screen } from "@testing-library/react";
import React from "react";

import { GroupControlMenu } from "./GroupControlMenu";

import { TestWrapper } from "TestWrapper";

describe("GroupControlMenu", () => {
  test("should render a component with essential props", function () {
    expect(() =>
      render(
        <GroupControlMenu
          groupId={1}
          anchorElem={null}
          handleClose={() => {
            /* do nothing */
          }}
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
      <GroupControlMenu
        groupId={1}
        anchorElem={document.createElement("button")}
        handleClose={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // menu items text should be displayed
    expect(screen.getByText("グループ編集")).toBeInTheDocument();
    expect(screen.getByText("削除")).toBeInTheDocument();
  });

  test("anchorElem is null, menu is closed", () => {
    const { container } = render(
      <GroupControlMenu groupId={1} anchorElem={null} handleClose={() => {}} />,
      { wrapper: TestWrapper },
    );

    // menu should be closed, so menu items should not be displayed
    const menuItems = container.querySelectorAll(".MuiMenuItem-root");
    expect(menuItems.length).toBe(0);
  });
});
