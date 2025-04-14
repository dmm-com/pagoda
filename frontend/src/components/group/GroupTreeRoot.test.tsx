/**
 * @jest-environment jsdom
 */

import { render, screen } from "@testing-library/react";
import React from "react";

import { TestWrapper } from "../../TestWrapper";
import { GroupTree } from "../../repository/AironeApiClient";
import { ServerContext } from "../../services/ServerContext";

import { GroupTreeRoot } from "./GroupTreeRoot";

// ServerContext のモック
jest.mock("../../services/ServerContext", () => {
  const mockInstance = {
    user: { isSuperuser: false },
  };
  return {
    ServerContext: {
      getInstance: jest.fn(() => mockInstance),
    },
  };
});

describe("GroupTreeRoot", () => {
  const groups: GroupTree[] = [
    {
      id: 1,
      name: "group1",
      children: [
        {
          id: 2,
          name: "group2",
          children: [],
        },
        {
          id: 3,
          name: "group3",
          children: [],
        },
      ],
    },
    {
      id: 4,
      name: "group4",
      children: [],
    },
  ];

  const baseProps = {
    groupTrees: groups,
    selectedGroupId: 1,
    handleSelectGroupId: () => {},
    setGroupAnchorEls: () => {},
  };

  afterEach(() => {
    // ステートをテストごとに初期化
    (ServerContext.getInstance as jest.Mock).mockReset();
  });

  test("renders correctly for general user (no menu buttons)", () => {
    // 一般ユーザとしてモックを上書き
    (ServerContext.getInstance as jest.Mock).mockReturnValue({
      user: { isSuperuser: false },
    });

    render(<GroupTreeRoot {...baseProps} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("checkbox")).toHaveLength(4);
    expect(screen.getAllByRole("checkbox")[0]).toBeChecked();

    // 一般ユーザは操作ボタンが表示されない想定
    expect(screen.queryAllByRole("button")).toHaveLength(0);
  });

  test("renders correctly for superuser (menu buttons shown)", () => {
    (ServerContext.getInstance as jest.Mock).mockReturnValue({
      user: { isSuperuser: true },
    });

    render(<GroupTreeRoot {...baseProps} />, { wrapper: TestWrapper });

    expect(screen.getAllByRole("checkbox")).toHaveLength(4);
    expect(screen.getAllByRole("checkbox")[0]).toBeChecked();

    // スーパーユーザの場合は、4つのグループそれぞれにボタンがある想定
    expect(screen.getAllByRole("button")).toHaveLength(4);
  });
});
