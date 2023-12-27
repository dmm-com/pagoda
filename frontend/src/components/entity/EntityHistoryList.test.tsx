/**
 * @jest-environment jsdom
 */

import { PaginatedEntityHistoryList } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen, within } from "@testing-library/react";
import React from "react";

import { EntityHistoryList, TargetOperation } from "./EntityHistoryList";

import { TestWrapper } from "TestWrapper";

describe("EntityHistoryList", () => {
  const histories: PaginatedEntityHistoryList = {
    count: 6,
    results: [
      {
        operation: TargetOperation.ADD_ENTITY,
        time: new Date("2020/01/01 00:00:00"),
        username: "user1",
        text: "entity1",
        targetObj: "entity1",
        isDetail: false,
      },
      {
        operation: TargetOperation.MOD_ENTITY,
        time: new Date("2020/01/02 00:00:00"),
        username: "user2",
        text: "entity1",
        targetObj: "entity1",
        isDetail: false,
      },
      {
        operation: TargetOperation.ADD_ATTR,
        time: new Date("2020/01/03 00:00:00"),
        username: "user3",
        text: "entity1",
        targetObj: "attr1",
        isDetail: false,
      },
      {
        operation: TargetOperation.MOD_ATTR,
        time: new Date("2020/01/04 00:00:00"),
        username: "user4",
        text: "entity1",
        targetObj: "attr1",
        isDetail: false,
      },
      {
        operation: TargetOperation.DEL_ATTR,
        time: new Date("2020/01/05 00:00:00"),
        username: "user5",
        text: "entity1",
        targetObj: "attr1_deleted_20200105000000",
        isDetail: false,
      },
      {
        operation: TargetOperation.DEL_ENTITY,
        time: new Date("2020/01/06 00:00:00"),
        username: "user6",
        text: "entity1",
        targetObj: "entity1",
        isDetail: false,
      },
    ],
  };

  test("should render entity histories", () => {
    const changePage = jest.fn();

    render(
      <EntityHistoryList
        histories={histories}
        page={1}
        changePage={changePage}
      />,
      { wrapper: TestWrapper }
    );

    const tableBody = screen.getAllByRole("rowgroup")[1];
    const historyRows = within(tableBody).getAllByRole("row");
    expect(historyRows).toHaveLength(6);
    expect(within(historyRows[0]).queryByText("作成")).toBeInTheDocument();
    expect(within(historyRows[1]).queryByText("変更")).toBeInTheDocument();
    expect(within(historyRows[2]).queryByText("属性追加")).toBeInTheDocument();
    expect(within(historyRows[2]).queryByText("attr1")).toBeInTheDocument();
    expect(within(historyRows[3]).queryByText("属性変更")).toBeInTheDocument();
    expect(within(historyRows[3]).queryByText("attr1")).toBeInTheDocument();
    expect(within(historyRows[4]).queryByText("属性削除")).toBeInTheDocument();
    expect(within(historyRows[4]).queryAllByText("attr1")).toHaveLength(2);
    expect(within(historyRows[5]).queryByText("削除")).toBeInTheDocument();

  });
});
