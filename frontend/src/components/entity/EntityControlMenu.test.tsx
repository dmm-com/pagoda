/**
 * @jest-environment jsdom
 */

import { render, screen } from "@testing-library/react";
import React from "react";

import { EntityControlMenu } from "./EntityControlMenu";

import { TestWrapper } from "TestWrapper";

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
});
