/**
 * @jest-environment jsdom
 */

import { render, screen } from "@testing-library/react";

import { CategoryControlMenu } from "./CategoryControlMenu";

import { TestWrapper } from "TestWrapper";
import { ACLType } from "services/ACLUtil";

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

  describe("permission-based visibility", () => {
    const defaultProps = {
      categoryId: 1,
      anchorElem: document.createElement("button"),
      handleClose: jest.fn(),
    };

    describe("when permission is Readable", () => {
      test("all operation menus should not be displayed", () => {
        render(
          <CategoryControlMenu
            {...defaultProps}
            permission={ACLType.Readable}
          />,
          { wrapper: TestWrapper },
        );

        expect(screen.queryByText("編集")).not.toBeInTheDocument();
        expect(screen.queryByText("ACL 設定")).not.toBeInTheDocument();
        expect(screen.queryByText("削除")).not.toBeInTheDocument();
      });
    });

    describe("when permission is Writable", () => {
      test("edit menu should be displayed", () => {
        render(
          <CategoryControlMenu
            {...defaultProps}
            permission={ACLType.Writable}
          />,
          { wrapper: TestWrapper },
        );

        expect(screen.getByText("編集")).toBeInTheDocument();
      });

      test("ACL and delete menus should not be displayed", () => {
        render(
          <CategoryControlMenu
            {...defaultProps}
            permission={ACLType.Writable}
          />,
          { wrapper: TestWrapper },
        );

        expect(screen.queryByText("ACL 設定")).not.toBeInTheDocument();
        expect(screen.queryByText("削除")).not.toBeInTheDocument();
      });
    });

    describe("when permission is Full", () => {
      test("all operation menus should be displayed", () => {
        render(
          <CategoryControlMenu {...defaultProps} permission={ACLType.Full} />,
          { wrapper: TestWrapper },
        );

        expect(screen.getByText("編集")).toBeInTheDocument();
        expect(screen.getByText("ACL 設定")).toBeInTheDocument();
        expect(screen.getByText("削除")).toBeInTheDocument();
      });
    });

    describe("when permission is undefined", () => {
      test("all menus should be displayed (backward compatibility)", () => {
        render(
          <CategoryControlMenu {...defaultProps} permission={undefined} />,
          { wrapper: TestWrapper },
        );

        expect(screen.getByText("編集")).toBeInTheDocument();
        expect(screen.getByText("ACL 設定")).toBeInTheDocument();
        expect(screen.getByText("削除")).toBeInTheDocument();
      });
    });
  });
});
