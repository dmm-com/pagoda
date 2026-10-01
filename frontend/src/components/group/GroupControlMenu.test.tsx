/**
 */

import { act, render, screen } from "@testing-library/react";

import { GroupControlMenu } from "./GroupControlMenu";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";

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

  test("renders menu items in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });

    render(
      <GroupControlMenu
        groupId={1}
        anchorElem={document.createElement("button")}
        handleClose={() => {}}
      />,
      { wrapper: TestWrapper },
    );

    expect(screen.getByText("Edit group")).toBeInTheDocument();
    expect(screen.getByText("Delete")).toBeInTheDocument();
  });
});
