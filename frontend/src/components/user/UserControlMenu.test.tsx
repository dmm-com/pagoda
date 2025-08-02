/**
 * @jest-environment jsdom
 */

import { render, screen } from "@testing-library/react";

import { UserControlMenu } from "./UserControlMenu";

import { TestWrapper } from "TestWrapper";

describe("UserControlMenu", () => {
  // dummy user data for testing
  const mockUser = {
    id: 1,
    username: "testuser",
    email: "test@example.com",
    isSuperuser: false,
    dateJoined: "2023-01-01T00:00:00Z",
  };

  test("should render a component with essential props", function () {
    expect(() =>
      render(
        <UserControlMenu
          user={mockUser}
          anchorElem={null}
          handleClose={() => {}}
          onClickEditPassword={() => {}}
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
      <UserControlMenu
        user={mockUser}
        anchorElem={document.createElement("button")}
        handleClose={() => {}}
        onClickEditPassword={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // menu items text should be displayed
    expect(screen.getByText("パスワード編集")).toBeInTheDocument();
    expect(screen.getByText("削除")).toBeInTheDocument();
  });

  test("anchorElem is null, menu is closed", () => {
    const { container } = render(
      <UserControlMenu
        user={mockUser}
        anchorElem={null}
        handleClose={() => {}}
        onClickEditPassword={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    // menu should be closed, so menu items should not be displayed
    const menuItems = container.querySelectorAll(".MuiMenuItem-root");
    expect(menuItems.length).toBe(0);
  });

  test("setToggle prop is optional", () => {
    // setToggle is optional
    expect(() =>
      render(
        <UserControlMenu
          user={mockUser}
          anchorElem={document.createElement("button")}
          handleClose={() => {}}
          onClickEditPassword={() => {}}
          setToggle={() => {}}
        />,
        { wrapper: TestWrapper },
      ),
    ).not.toThrow();
  });
});
