/**
 * @jest-environment jsdom
 */

import { render, screen } from "@testing-library/react";

import { CategoryControlMenu } from "./CategoryControlMenu";

import { TestWrapper } from "TestWrapper";

describe("CategoryControlMenu", () => {
  test("renders without crashing", () => {
    const handleClose = jest.fn();

    expect(() =>
      render(
        <CategoryControlMenu
          categoryId={1}
          anchorElem={document.createElement("button")}
          handleClose={handleClose}
        />,
        { wrapper: TestWrapper },
      ),
    ).not.toThrow();
  });

  test("menu items are displayed correctly", () => {
    // specify anchorElem to open the menu
    render(
      <CategoryControlMenu
        categoryId={1}
        anchorElem={document.createElement("button")}
        handleClose={jest.fn()}
      />,
      { wrapper: TestWrapper },
    );

    // menu items text should be displayed
    expect(screen.getByText("編集")).toBeInTheDocument();
    expect(screen.getByText("ACL 設定")).toBeInTheDocument();
    expect(screen.getByText("削除")).toBeInTheDocument();
  });

  test("anchorElem is null, menu is closed", () => {
    const { container } = render(
      <CategoryControlMenu
        categoryId={1}
        anchorElem={null}
        handleClose={jest.fn()}
      />,
      { wrapper: TestWrapper },
    );

    // menu should be closed, so menu items should not be displayed
    const menuItems = container.querySelectorAll(".MuiMenuItem-root");
    expect(menuItems.length).toBe(0);
  });
});
