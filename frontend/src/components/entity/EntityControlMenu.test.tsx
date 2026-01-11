/**
 * @jest-environment jsdom
 */

import { render, screen } from "@testing-library/react";

import { EntityControlMenu } from "./EntityControlMenu";

import { TestWrapper } from "TestWrapper";
import { ACLType } from "services/ACLUtil";

describe("EntityControlMenu", () => {
  test("should render with essential props", () => {
    expect(() =>
      render(
        <EntityControlMenu
          entityId={1}
          anchorElem={null}
          handleClose={() => {
            /* any closing process */
          }}
          setOpenImportModal={() => false}
        />,
        { wrapper: TestWrapper },
      ),
    ).not.toThrow();
  });

  test("menu items are displayed correctly", () => {
    // specify anchorElem to open the menu
    render(
      <EntityControlMenu
        entityId={1}
        anchorElem={document.createElement("button")}
        handleClose={() => {}}
        setOpenImportModal={() => false}
      />,
      { wrapper: TestWrapper },
    );

    // menu items text should be displayed
    expect(screen.getByText("アイテム一覧")).toBeInTheDocument();
    expect(screen.getByText("エイリアス一覧")).toBeInTheDocument();
    expect(screen.getByText("編集")).toBeInTheDocument();
    expect(screen.getByText("ACL 設定")).toBeInTheDocument();
    expect(screen.getByText("変更履歴")).toBeInTheDocument();
    expect(screen.getByText("ACL 変更履歴")).toBeInTheDocument();
    expect(screen.getByText("エクスポート(YAML)")).toBeInTheDocument();
    expect(screen.getByText("エクスポート(CSV)")).toBeInTheDocument();
    expect(screen.getByText("インポート")).toBeInTheDocument();
    expect(screen.getByText("削除アイテムの復旧")).toBeInTheDocument();
    expect(screen.getByText("削除")).toBeInTheDocument();
  });

  test("anchorElem is null, menu is closed", () => {
    const { container } = render(
      <EntityControlMenu
        entityId={1}
        anchorElem={null}
        handleClose={() => {}}
        setOpenImportModal={() => false}
      />,
      { wrapper: TestWrapper },
    );

    // menu should be closed, so menu items should not be displayed
    const menuItems = container.querySelectorAll(".MuiMenuItem-root");
    expect(menuItems.length).toBe(0);
  });

  describe("permission-based visibility", () => {
    const defaultProps = {
      entityId: 1,
      anchorElem: document.createElement("button"),
      handleClose: () => {},
      setOpenImportModal: () => false,
    };

    describe("when permission is Readable", () => {
      test("edit and import menus should not be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Readable} />,
          { wrapper: TestWrapper },
        );

        expect(screen.queryByText("編集")).not.toBeInTheDocument();
        expect(screen.queryByText("インポート")).not.toBeInTheDocument();
      });

      test("ACL and delete menus should not be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Readable} />,
          { wrapper: TestWrapper },
        );

        expect(screen.queryByText("ACL 設定")).not.toBeInTheDocument();
        expect(screen.queryByText("削除")).not.toBeInTheDocument();
      });

      test("read-only menus should still be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Readable} />,
          { wrapper: TestWrapper },
        );

        expect(screen.getByText("アイテム一覧")).toBeInTheDocument();
        expect(screen.getByText("エイリアス一覧")).toBeInTheDocument();
        expect(screen.getByText("変更履歴")).toBeInTheDocument();
        expect(screen.getByText("ACL 変更履歴")).toBeInTheDocument();
        expect(screen.getByText("エクスポート(YAML)")).toBeInTheDocument();
        expect(screen.getByText("エクスポート(CSV)")).toBeInTheDocument();
        expect(screen.getByText("削除アイテムの復旧")).toBeInTheDocument();
      });
    });

    describe("when permission is Writable", () => {
      test("edit and import menus should be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Writable} />,
          { wrapper: TestWrapper },
        );

        expect(screen.getByText("編集")).toBeInTheDocument();
        expect(screen.getByText("インポート")).toBeInTheDocument();
      });

      test("ACL and delete menus should not be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Writable} />,
          { wrapper: TestWrapper },
        );

        expect(screen.queryByText("ACL 設定")).not.toBeInTheDocument();
        expect(screen.queryByText("削除")).not.toBeInTheDocument();
      });
    });

    describe("when permission is Full", () => {
      test("all operation menus should be displayed", () => {
        render(
          <EntityControlMenu {...defaultProps} permission={ACLType.Full} />,
          { wrapper: TestWrapper },
        );

        expect(screen.getByText("アイテム一覧")).toBeInTheDocument();
        expect(screen.getByText("編集")).toBeInTheDocument();
        expect(screen.getByText("ACL 設定")).toBeInTheDocument();
        expect(screen.getByText("インポート")).toBeInTheDocument();
        expect(screen.getByText("削除")).toBeInTheDocument();
      });
    });

    describe("when permission is undefined", () => {
      test("all menus should be displayed (backward compatibility)", () => {
        render(<EntityControlMenu {...defaultProps} permission={undefined} />, {
          wrapper: TestWrapper,
        });

        expect(screen.getByText("編集")).toBeInTheDocument();
        expect(screen.getByText("ACL 設定")).toBeInTheDocument();
        expect(screen.getByText("インポート")).toBeInTheDocument();
        expect(screen.getByText("削除")).toBeInTheDocument();
      });
    });
  });
});
