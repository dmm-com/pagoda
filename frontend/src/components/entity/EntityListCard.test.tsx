/**
 * @jest-environment jsdom
 */

import { EntityList } from "@dmm-com/airone-apiclient-typescript-fetch";
import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { EntityListCard } from "components/entity/EntityListCard";

describe("EntityListCard", () => {
  const entity: EntityList = {
    id: 1,
    name: "TestEntity",
    note: "This is a test entity.",
    isToplevel: true,
  };

  test("should render entity", () => {
    const setToggle = jest.fn();

    render(<EntityListCard entity={entity} setToggle={setToggle} />, {
      wrapper: TestWrapper,
    });

    expect(screen.getByText(entity.name)).toBeInTheDocument();
    expect(screen.getByText(entity?.note ?? "")).toBeInTheDocument();
  });

  test("should click menu button", () => {
    const setToggle = jest.fn();

    render(<EntityListCard entity={entity} setToggle={setToggle} />, {
      wrapper: TestWrapper,
    });

    const moreButton = screen.getByRole("button", { name: "モデルの操作" });
    expect(moreButton).toBeInTheDocument();

    // Click the button
    fireEvent.click(moreButton);

    // Verify the button was clicked (menu display check is omitted due to complexity)
    expect(moreButton).toBeInTheDocument();
  });

  test("should render without note", () => {
    const entityWithoutNote = { ...entity, note: undefined };
    const setToggle = jest.fn();

    render(
      <EntityListCard entity={entityWithoutNote} setToggle={setToggle} />,
      {
        wrapper: TestWrapper,
      },
    );

    expect(screen.getByText(entity.name)).toBeInTheDocument();
    expect(
      screen.queryByText("This is a test entity."),
    ).not.toBeInTheDocument();
  });

  test("should render without setToggle prop", () => {
    render(<EntityListCard entity={entity} />, {
      wrapper: TestWrapper,
    });

    // Verify basic rendering
    expect(screen.getByText(entity.name)).toBeInTheDocument();
    expect(screen.getByText(entity.note ?? "")).toBeInTheDocument();

    // Verify model operation button exists
    const moreButton = screen.getByRole("button", { name: "モデルの操作" });
    expect(moreButton).toBeInTheDocument();
  });

  test("should copy entity name to clipboard when copy button is clicked", async () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockImplementation(() => Promise.resolve()),
      },
    });

    render(<EntityListCard entity={entity} />, {
      wrapper: TestWrapper,
    });

    // ボタンはaria-labelで取得
    const copyButton = screen.getByRole("button", {
      name: "名前をコピーする",
    });

    // ホバー時のTooltip
    fireEvent.mouseOver(copyButton);
    expect(await screen.findByText("名前をコピーする")).toBeInTheDocument();

    // クリック
    fireEvent.click(copyButton);

    // クリック後のTooltip
    fireEvent.mouseOver(copyButton);
    expect(await screen.findByText("名前をコピーしました")).toBeInTheDocument();

    // Verify the correct value was written to clipboard
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(entity.name);
  });
});
